#!/usr/bin/env python3
"""
arch-check.py — 架构分层合规检查（通用版）

用法：
    python3 governance/arch-check.py [--src <src-dir>]

功能：
    1. 读取项目根目录的 CONSTITUTION.md，提取架构红线规则
    2. 扫描源代码目录（默认：src/，backend/app/，app/），用 AST 检查 import
    3. 报告违反分层规则的 import
    4. 所有检查通过则退出码 0，否则退出码 1

规则来源：
    优先从 CONSTITUTION.md 中的「架构红线」章节读取规则。
    如果读取失败，使用内置默认规则（models > services > api，见下方）。

内置默认规则（当 CONSTITUTION.md 未配置时使用）：
    models/   → 禁止 import api/, services/
    services/ → 禁止 import api/
    tasks/    → 禁止 import api/
    api/      → 无限制
"""

import ast
import sys
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# 默认架构规则（fallback）
# ---------------------------------------------------------------------------

DEFAULT_LAYER_RULES: dict[str, dict] = {
    "models": {"forbidden": ["app.api", "app.services", ".api.", ".services."]},
    "services": {"forbidden": ["app.api", ".api."]},
    "tasks": {"forbidden": ["app.api", ".api."]},
    "api": {"forbidden": []},
}


# ---------------------------------------------------------------------------
# 从 CONSTITUTION.md 读取自定义规则
# ---------------------------------------------------------------------------

def parse_constitution_rules(constitution_path: Path) -> dict[str, dict] | None:
    """
    从 CONSTITUTION.md 解析架构规则。
    识别格式：
        ### 分层架构规则
        ```
        API 层 (api/)
          └── 禁止：...
        Services 层 (services/)
          └── 禁止：...
        ```
    返回规则字典，解析失败返回 None。
    """
    if not constitution_path.exists():
        return None

    content = constitution_path.read_text(encoding="utf-8")

    # 找到「分层架构规则」章节
    section_match = re.search(
        r"#{1,4}\s*分层架构规则.*?\n(.*?)(?=#{1,4}|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not section_match:
        return None

    section = section_match.group(1)
    rules: dict[str, dict] = {}

    # 解析每个层的禁止规则
    # 格式：  └── 禁止：app.api, app.services
    layer_pattern = re.compile(r"(\w+)\s*层\s*\((\w+)/\)", re.IGNORECASE)
    forbidden_pattern = re.compile(r"禁止[：:]\s*(.+)")

    current_layer = None
    for line in section.splitlines():
        layer_match = layer_pattern.search(line)
        if layer_match:
            current_layer = layer_match.group(2).lower()
            rules.setdefault(current_layer, {"forbidden": []})

        if current_layer:
            forbidden_match = forbidden_pattern.search(line)
            if forbidden_match:
                forbidden_str = forbidden_match.group(1)
                # 排除「无」或「无限制」
                if "无" in forbidden_str:
                    continue
                # 解析逗号分隔的模块名
                items = [f.strip().rstrip("，,") for f in re.split(r"[，,、]", forbidden_str)]
                # 过滤掉中文描述（只保留含点或斜杠的模块名）
                module_items = [i for i in items if ("." in i or "/" in i) and i]
                rules[current_layer]["forbidden"].extend(module_items)

    return rules if rules else None


# ---------------------------------------------------------------------------
# AST 检查
# ---------------------------------------------------------------------------

def check_file(filepath: Path, layer_rules: dict[str, dict]) -> list[str]:
    """检查单个 Python 文件是否违反架构规则。"""
    errors: list[str] = []

    # 确定文件属于哪个层
    parts = filepath.parts
    layer = None
    for part in parts:
        if part.lower() in layer_rules:
            layer = part.lower()
            break

    if not layer:
        return errors

    # 解析 AST
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"⚠️  {filepath}: SyntaxError（跳过检查）: {e}"]

    forbidden_prefixes = layer_rules[layer].get("forbidden", [])
    if not forbidden_prefixes:
        return errors

    # 检查所有 import 语句
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for prefix in forbidden_prefixes:
                # 支持多种匹配模式：前缀匹配、包含匹配
                if (module.startswith(prefix) or
                        prefix in module or
                        module.startswith(prefix.lstrip("."))):
                    errors.append(
                        f"❌ {filepath}:{node.lineno} — "
                        f"`{layer}/` 不允许 import `{prefix}.*`，"
                        f"发现: from {module} import ..."
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                for prefix in forbidden_prefixes:
                    if (module.startswith(prefix) or
                            prefix in module or
                            module.startswith(prefix.lstrip("."))):
                        errors.append(
                            f"❌ {filepath}:{node.lineno} — "
                            f"`{layer}/` 不允许 import `{prefix}.*`，"
                            f"发现: import {module}"
                        )

    return errors


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def find_source_dirs(project_root: Path, explicit_src: str | None) -> list[Path]:
    """找到要扫描的源代码目录。"""
    if explicit_src:
        src = project_root / explicit_src
        if src.exists():
            return [src]
        print(f"⚠️  指定的源代码目录不存在: {src}")
        return []

    # 自动探测常见目录
    candidates = ["src", "backend/app", "app", "backend/src"]
    found = []
    for candidate in candidates:
        path = project_root / candidate
        if path.exists() and path.is_dir():
            found.append(path)

    return found


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="架构分层合规检查")
    parser.add_argument("--src", default=None, help="源代码目录（默认自动探测 src/, app/, backend/app/）")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 读取架构规则
    constitution_path = project_root / "CONSTITUTION.md"
    layer_rules = parse_constitution_rules(constitution_path)

    if layer_rules:
        print(f"📋 使用 CONSTITUTION.md 中的架构规则（{len(layer_rules)} 个层）")
    else:
        layer_rules = DEFAULT_LAYER_RULES
        if constitution_path.exists():
            print(f"⚠️  CONSTITUTION.md 中未找到分层架构规则，使用内置默认规则")
        else:
            print(f"⚠️  CONSTITUTION.md 不存在，使用内置默认规则")

    # 找到源代码目录
    src_dirs = find_source_dirs(project_root, args.src)

    if not src_dirs:
        print(f"⚠️  未找到源代码目录（src/, app/, backend/app/），跳过架构检查")
        print(f"   提示：使用 --src <目录> 指定源代码目录")
        sys.exit(0)

    print(f"🔍 扫描目录：{[str(d) for d in src_dirs]}")

    # 扫描所有 Python 文件
    all_errors: list[str] = []
    total_files = 0

    for src_dir in src_dirs:
        py_files = list(src_dir.rglob("*.py"))
        total_files += len(py_files)
        for py_file in py_files:
            errors = check_file(py_file, layer_rules)
            all_errors.extend(errors)

    print(f"   扫描了 {total_files} 个 Python 文件")

    # 输出结果
    if all_errors:
        print()
        print(f"架构分层检查失败（{len(all_errors)} 个违规）：")
        for err in all_errors:
            print(f"  {err}")
        print()
        print("修复建议：")
        print("  - 将跨层调用移到正确的层（例如：在 api/ 中调用 services/ 而非直接 import models/）")
        print("  - 或更新 CONSTITUTION.md 中的架构规则（需人工审批）")
        sys.exit(1)
    else:
        print(f"✅ 架构分层检查通过（{total_files} 个文件，无违规）")
        sys.exit(0)


if __name__ == "__main__":
    main()
