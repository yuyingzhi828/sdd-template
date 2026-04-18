#!/usr/bin/env python3
"""
impact.py — 评估变更影响范围

用法：
    python3 governance/impact.py <project-id> <ch-id>

示例：
    python3 governance/impact.py project-001 CH-001

功能：
    1. 读取变更的 delta.md，提取涉及的文件列表
    2. 读取 LOCK.md，对比哪些文件已锁定
    3. 扫描项目代码目录，找出 import/依赖关系（grep 方式，无需 AST）
    4. 生成 impact.md 并写入变更目录
    5. 打印风险等级摘要
"""

import fnmatch
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# 解析 delta.md：提取涉及的文件
# ---------------------------------------------------------------------------

def extract_files_from_delta(delta_path: Path) -> list[str]:
    """
    从 delta.md 中提取所有涉及的文件路径。
    支持两种格式：
      - Markdown 表格行（| `path/to/file` | ... |）
      - 反引号包裹的路径（`src/xxx/yyy.py`）
    """
    if not delta_path.exists():
        return []

    content = delta_path.read_text(encoding="utf-8")
    files: list[str] = []

    # 匹配反引号中看起来像文件路径的内容（含 / 或 .py/.md 等扩展名）
    pattern = re.compile(r"`([^`]+\.[a-zA-Z]{1,6})`")
    for match in pattern.finditer(content):
        candidate = match.group(1)
        # 过滤掉明显不是文件路径的内容（如 CH-NNN, REQ-NNN 等）
        if "/" in candidate or candidate.endswith((".py", ".md", ".yaml", ".yml", ".json", ".toml", ".sh")):
            if candidate not in files:
                files.append(candidate)

    return files


# ---------------------------------------------------------------------------
# 解析 LOCK.md：提取已锁定文件
# ---------------------------------------------------------------------------

def get_locked_files(lock_path: Path) -> list[dict]:
    """
    从 LOCK.md 解析已锁定文件表。
    返回列表，每项：{"path": str, "reason": str, "sprint": str}
    """
    if not lock_path.exists():
        return []

    locked: list[dict] = []
    in_table = False
    header_found = False

    for line in lock_path.read_text(encoding="utf-8").splitlines():
        # 识别已锁定文件表的表头
        if "文件路径" in line and "锁定原因" in line:
            in_table = True
            header_found = True
            continue
        # 跳过分隔行（| --- | --- |）
        if in_table and re.match(r"^\|[-| ]+\|$", line.strip()):
            continue
        # 解析表格数据行
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3:
                file_path = cells[0].strip("`").strip()
                reason = cells[1] if len(cells) > 1 else ""
                sprint = cells[3] if len(cells) > 3 else ""
                if file_path and file_path != "文件路径":
                    locked.append({"path": file_path, "reason": reason, "sprint": sprint})
        # 表格结束
        elif in_table and header_found and not line.startswith("|") and line.strip():
            if not line.startswith(">"):  # 忽略注释行
                in_table = False

    return locked


def is_locked(file_path: str, locked_files: list[dict]) -> dict | None:
    """检查文件是否在锁定列表中（支持 glob 匹配）。返回锁定条目或 None。"""
    for entry in locked_files:
        pattern = entry["path"]
        if "*" in pattern:
            if fnmatch.fnmatch(file_path, pattern):
                return entry
        else:
            if file_path == pattern or file_path.endswith(pattern) or pattern.endswith(file_path):
                return entry
    return None


# ---------------------------------------------------------------------------
# 扫描代码依赖（grep 方式）
# ---------------------------------------------------------------------------

def find_dependents(target_files: list[str], project_root: Path) -> dict[str, list[str]]:
    """
    扫描项目代码目录，找出哪些文件 import 了目标文件所在的模块。
    使用简单的字符串匹配，不做 AST 解析。

    返回：{target_file: [dependent_file, ...]}
    """
    dependents: dict[str, list[str]] = {f: [] for f in target_files}

    # 将文件路径转换为 Python 模块名（用于 import 匹配）
    def path_to_module(file_path: str) -> str:
        return file_path.replace("/", ".").replace("\\", ".").removesuffix(".py")

    # 扫描所有 Python 文件
    code_files = list(project_root.rglob("*.py"))

    for target_file in target_files:
        module_name = path_to_module(target_file)
        # 提取模块的最后几段，用于宽松匹配
        module_parts = module_name.split(".")
        short_module = ".".join(module_parts[-2:]) if len(module_parts) >= 2 else module_name

        for code_file in code_files:
            # 不检查目标文件自身
            relative = str(code_file.relative_to(project_root)) if project_root in code_file.parents else str(code_file)
            if relative == target_file or relative.replace("\\", "/") == target_file:
                continue

            try:
                content = code_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # 检查 import 语句（import xxx 或 from xxx import yyy）
            if short_module in content or module_name in content:
                # 进一步验证是 import 语句，不是注释或字符串中的随机出现
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if (f"import {short_module}" in stripped or
                            f"from {short_module}" in stripped or
                            f"import {module_name}" in stripped or
                            f"from {module_name}" in stripped):
                        rel = str(code_file.relative_to(project_root)) if project_root in code_file.parents else str(code_file)
                        if rel not in dependents[target_file]:
                            dependents[target_file].append(rel)
                        break

    return dependents


# ---------------------------------------------------------------------------
# 风险等级判断
# ---------------------------------------------------------------------------

def assess_risk(locked_hits: list[dict]) -> tuple[str, str]:
    """
    根据锁定文件命中数量和类型评估风险等级。
    返回：(level, explanation)
    """
    if not locked_hits:
        return "低", "未触及任何锁定文件，影响范围明确"
    if len(locked_hits) == 1:
        return "中", f"触及 1 个锁定文件（{locked_hits[0]['path']}），影响范围相对明确，需申请解锁"
    return "高", f"触及 {len(locked_hits)} 个锁定文件，影响范围较广，建议等待相关 Sprint 归档后实施"


# ---------------------------------------------------------------------------
# 生成 impact.md
# ---------------------------------------------------------------------------

def generate_impact_md(
    ch_id: str,
    delta_files: list[str],
    locked_hits: list[dict],
    lock_status: list[dict],
    dependents: dict[str, list[str]],
    risk_level: str,
    risk_explanation: str,
    now: str,
) -> str:
    """生成 impact.md 内容。"""

    # LOCK 扫描结果表
    lock_rows = []
    for entry in lock_status:
        file_path = entry["file"]
        locked = entry["locked"]
        sprint = entry.get("sprint", "-")
        if locked:
            impact = "高（需修改锁定文件）" if "model" in file_path.lower() else "中（涉及锁定模块）"
            lock_rows.append(f"| `{file_path}` | 🔒 锁定中 | {sprint} | {impact} |")
        else:
            lock_rows.append(f"| `{file_path}` | ✅ 未锁定 | - | 低 |")

    lock_table = "\n".join(lock_rows) if lock_rows else "| （delta.md 中未检测到文件路径） | - | - | - |"

    # 模块影响分析
    module_rows = []
    for f in delta_files:
        deps = dependents.get(f, [])
        dep_count = len(deps)
        impact_type = "Schema/接口变更" if any(x in f for x in ["model", "schema", "api"]) else "逻辑变更"
        module_rows.append(f"| `{f}` | **{impact_type}** | {dep_count} 个文件依赖 |")

    module_table = "\n".join(module_rows) if module_rows else "| （未检测到文件） | - | - |"

    # 下游依赖
    downstream_rows = []
    for target, deps in dependents.items():
        for dep in deps:
            downstream_rows.append(f"| `{target}` | `{dep}` | 该文件 import 了受影响模块 |")

    downstream_table = "\n".join(downstream_rows) if downstream_rows else "| （未检测到下游依赖） | - | - |"

    # 解锁申请建议
    unlock_rows = []
    for h in locked_hits:
        unlock_rows.append(f"| `{h['path']}` | 在 LOCK.md 解锁申请表中登记，等待相关 Sprint 负责人确认 |")

    unlock_table = "\n".join(unlock_rows) if unlock_rows else "| （无需解锁申请） | - |"

    # 风险等级勾选
    risk_low = "[x]" if risk_level == "低" else "[ ]"
    risk_mid = "[x]" if risk_level == "中" else "[ ]"
    risk_high = "[x]" if risk_level == "高" else "[ ]"

    # 审批建议
    if risk_level == "低":
        approval = "✅ 低风险变更\n\n建议：可直接执行 apply 操作，实施后注意更新 RFC.md。"
    elif risk_level == "中":
        approval = (
            "⚠️  中风险变更\n\n建议：\n"
            + "\n".join(f"  {i+1}. 申请解锁 `{h['path']}`" for i, h in enumerate(locked_hits))
            + "\n  - 解锁申请审批通过后，再执行 apply 操作"
            + "\n  - 实施完成后及时将 delta.md 合并回 RFC.md"
        )
    else:
        approval = (
            "🚨 高风险变更\n\n建议：\n"
            "  1. 召集相关 Sprint 负责人进行评审\n"
            "  2. 考虑拆分为多个小变更分批实施\n"
            "  3. 确保有完整的回滚方案\n"
            "  4. 所有锁定文件的解锁申请审批通过后方可实施"
        )

    return f"""# {ch_id} Impact Assessment

> **说明**：本文件由 `python3 governance/impact.py` 自动生成。
> 人工审查后，通过 `apply-and-archive.py apply` 确认实施。

---

## LOCK 扫描结果

| 文件 | 锁定状态 | 锁定 Sprint | 影响程度 |
|-----|---------|-----------|---------|
{lock_table}

---

## 模块影响分析

| 模块 | 影响类型 | 下游依赖数 |
|------|---------|---------|
{module_table}

---

## 下游依赖

| 受影响模块 | 依赖它的模块 | 风险说明 |
|---------|-----------|---------|
{downstream_table}

---

## 风险等级

- {risk_low} **低**（不触及任何锁定文件，影响范围明确）
- {risk_mid} **中**（触及锁定文件，但影响范围明确，有缓解措施）
- {risk_high} **高**（触及多个锁定文件或核心架构，需要特别评审）

**风险说明**：
```
{risk_explanation}
```

---

## 解锁申请建议

| 文件 | 建议操作 |
|------|---------|
{unlock_table}

---

## 审批建议

```
{approval}
```

---

## 生成信息

- **生成时间**：{now}
- **生成工具**：`governance/impact.py`
- **扫描文件数**：{len(delta_files)} 个
- **锁定命中数**：{len(locked_hits)} 个
"""


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 3:
        print("用法：python3 governance/impact.py <project-id> <ch-id>")
        print("示例：python3 governance/impact.py project-001 CH-001")
        sys.exit(1)

    project_id = sys.argv[1]
    ch_id = sys.argv[2].upper()
    if not ch_id.startswith("CH-"):
        ch_id = f"CH-{ch_id}"

    # 路径解析
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    project_dir = project_root / "specs" / project_id
    change_dir = project_dir / "changes" / "active" / ch_id

    # 检查必要文件
    delta_path = change_dir / "delta.md"
    lock_path = project_dir / "LOCK.md"

    if not change_dir.exists():
        print(f"❌ 变更目录不存在: {change_dir}")
        print(f"   请先运行：python3 governance/propose.py {project_id} \"变更标题\"")
        sys.exit(1)

    if not delta_path.exists():
        print(f"❌ delta.md 不存在: {delta_path}")
        print(f"   请先运行 propose.py 生成变更目录，或手动创建 delta.md")
        sys.exit(1)

    print(f"🔍 分析变更影响：{ch_id}")
    print(f"   项目：{project_id}")
    print(f"   Delta：{delta_path}")
    print()

    # 1. 提取 delta.md 中的文件列表
    delta_files = extract_files_from_delta(delta_path)
    print(f"📄 delta.md 中检测到 {len(delta_files)} 个文件：")
    for f in delta_files:
        print(f"   - {f}")
    print()

    # 2. 读取 LOCK.md
    locked_files = get_locked_files(lock_path)
    print(f"🔒 LOCK.md 中有 {len(locked_files)} 个锁定文件")

    # 3. 对比锁定状态
    lock_status: list[dict] = []
    locked_hits: list[dict] = []
    for f in delta_files:
        entry = is_locked(f, locked_files)
        if entry:
            lock_status.append({"file": f, "locked": True, "sprint": entry.get("sprint", "")})
            locked_hits.append({"path": f, "sprint": entry.get("sprint", "")})
        else:
            lock_status.append({"file": f, "locked": False})

    if locked_hits:
        print(f"⚠️  发现 {len(locked_hits)} 个锁定文件冲突：")
        for h in locked_hits:
            print(f"   🔒 {h['path']} (sprint: {h['sprint']})")
    else:
        print("✅ 无锁定文件冲突")
    print()

    # 4. 扫描代码依赖
    print("🔗 扫描代码依赖关系...")
    dependents = find_dependents(delta_files, project_root)
    total_deps = sum(len(v) for v in dependents.values())
    print(f"   检测到 {total_deps} 个下游依赖文件")
    print()

    # 5. 评估风险等级
    risk_level, risk_explanation = assess_risk(locked_hits)
    print(f"📊 风险等级：{risk_level}")
    print(f"   {risk_explanation}")
    print()

    # 6. 生成 impact.md
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    impact_content = generate_impact_md(
        ch_id, delta_files, locked_hits, lock_status,
        dependents, risk_level, risk_explanation, now
    )
    impact_path = change_dir / "impact.md"
    impact_path.write_text(impact_content, encoding="utf-8")

    print(f"✅ impact.md 已生成：{impact_path}")
    print()
    print("下一步：")
    print(f"  1. 查看 impact.md，确认影响范围")
    if locked_hits:
        print(f"  2. 在 LOCK.md 中提交解锁申请（解锁申请表）")
        print(f"  3. 等待解锁审批后：python3 governance/apply-and-archive.py {project_id} {ch_id} apply")
    else:
        print(f"  2. 确认无误后：python3 governance/apply-and-archive.py {project_id} {ch_id} apply")


if __name__ == "__main__":
    main()
