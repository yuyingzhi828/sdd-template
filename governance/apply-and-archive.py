#!/usr/bin/env python3
"""
apply-and-archive.py — 推进变更状态

用法：
    python3 governance/apply-and-archive.py <project-id> <ch-id> apply
    python3 governance/apply-and-archive.py <project-id> <ch-id> archive

apply 阶段（draft → in-progress）：
  - 检查 proposal.md 状态为 draft
  - 检查 delta.md 是否已填写（不是纯模板）
  - 检查 impact.md 是否存在
  - 交互确认后，将 proposal.md 状态更新为 in-progress

archive 阶段（in-progress → archived）：
  - 检查状态为 in-progress
  - 检查 tasks.md 未完成项数量（如存在），有未完成项则警告
  - 交互确认后，移动到 archive/ 目录
  - 追加 RFC_CHANGELOG.md
  - 提示手动合并 delta.md 回 RFC.md
"""

import re
import shutil
import sys
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def read_file(path: Path) -> str:
    """读取文件内容，文件不存在时返回空字符串。"""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def update_status_in_proposal(proposal_path: Path, new_status: str) -> bool:
    """将 proposal.md 中的「当前状态」行更新为新状态。"""
    content = read_file(proposal_path)
    if not content:
        return False

    # 匹配形如：- **当前状态**：draft 或 - **当前状态**: draft
    pattern = re.compile(
        r"(-\s*\*\*当前状态\*\*[：:]\s*)(draft|in-progress|archived)",
        re.IGNORECASE
    )
    new_content, count = pattern.subn(lambda m: m.group(1) + new_status, content)
    if count == 0:
        # 尝试更宽松的匹配
        pattern2 = re.compile(r"(当前状态[：:]\s*)(draft|in-progress|archived)", re.IGNORECASE)
        new_content, count = pattern2.subn(lambda m: m.group(1) + new_status, content)

    if count > 0:
        proposal_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def get_current_status(proposal_path: Path) -> str:
    """从 proposal.md 中读取当前状态。"""
    content = read_file(proposal_path)
    for pattern in [
        r"当前状态[：:]\s*(draft|in-progress|archived)",
        r"\*\*当前状态\*\*[：:]\s*(draft|in-progress|archived)",
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            return m.group(1).lower()
    return "unknown"


def is_template_only(content: str, placeholder_patterns: list[str]) -> bool:
    """检查文件是否仍是纯模板（只有占位符，没有实际内容）。"""
    # 如果包含占位符 AI 生成内容标记，视为未填写
    if "[AI 生成内容占位符]" in content:
        return True
    # 如果所有关键占位符仍然存在，视为未填写
    unfilled = sum(1 for p in placeholder_patterns if p in content)
    return unfilled >= len(placeholder_patterns) * 0.8  # 超过 80% 的占位符未填写则认为是模板


def count_incomplete_tasks(tasks_md_content: str) -> int:
    """统计 TASKS.md 中未完成的任务数（状态为「待开始」或「进行中」）。"""
    count = 0
    for line in tasks_md_content.splitlines():
        if "🔲" in line or "待开始" in line or "🔄" in line or "进行中" in line:
            # 确保是任务行（包含 TK- 编号）
            if re.search(r"TK-\d+", line):
                count += 1
    return count


def confirm(prompt: str) -> bool:
    """交互式确认，返回用户是否确认。"""
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
        return answer in ("y", "yes", "是")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def append_to_changelog(changelog_path: Path, ch_id: str, title: str, project_id: str) -> None:
    """追加一条记录到 RFC_CHANGELOG.md。"""
    today = date.today().isoformat()
    entry = f"""
---

### {ch_id}: {title}（{today} 归档）

- **变更标题**：{title}
- **提案时间**：（见 proposal.md）
- **归档时间**：{today}
- **实施 Sprint**：（请手动填写）
- **涉及需求**：（请从 delta.md 同步）
- **实施结果**：（请填写：✅ 完整实施 / ⚠️ 部分实施 / ❌ 未实施）
- **遗留事项**：（请填写）
- **归档人**：（请填写）

"""
    existing = read_file(changelog_path)
    # 追加到文件末尾（在最后一个 --- 之后）
    with changelog_path.open("a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# apply 阶段
# ---------------------------------------------------------------------------

def do_apply(project_dir: Path, ch_id: str) -> None:
    """执行 apply 操作：draft → in-progress。"""
    change_dir = project_dir / "changes" / "active" / ch_id
    proposal_path = change_dir / "proposal.md"
    delta_path = change_dir / "delta.md"
    impact_path = change_dir / "impact.md"

    print(f"🔍 检查变更 {ch_id} 的就绪状态...\n")

    # 检查目录和文件存在
    if not change_dir.exists():
        print(f"❌ 变更目录不存在: {change_dir}")
        sys.exit(1)

    if not proposal_path.exists():
        print(f"❌ proposal.md 不存在: {proposal_path}")
        sys.exit(1)

    # 检查 1：proposal.md 状态必须是 draft
    current_status = get_current_status(proposal_path)
    if current_status == "in-progress":
        print(f"⚠️  proposal.md 已经是 in-progress 状态，无需再次 apply")
        sys.exit(0)
    if current_status == "archived":
        print(f"❌ 变更已归档，无法再次 apply")
        sys.exit(1)
    if current_status not in ("draft", "unknown"):
        print(f"❌ 未知状态：{current_status}（期望：draft）")
        sys.exit(1)
    print(f"  ✅ proposal.md 状态：{current_status}")

    # 检查 2：delta.md 是否已填写
    if not delta_path.exists():
        print(f"  ❌ delta.md 不存在，请先填写变更内容")
        sys.exit(1)

    delta_content = read_file(delta_path)
    placeholder_patterns = ["<需求描述>", "<需求标题>", "<文件路径>", "REQ-NNN"]
    if is_template_only(delta_content, placeholder_patterns):
        print(f"  ⚠️  delta.md 看起来仍是纯模板，请填写具体的变更内容")
        print(f"       文件：{delta_path}")
        if not confirm("  delta.md 可能未填写完整，仍要继续吗？"):
            print("已取消。请先完善 delta.md 后重试。")
            sys.exit(0)
    else:
        print(f"  ✅ delta.md 已填写")

    # 检查 3：impact.md 是否存在
    if not impact_path.exists():
        print(f"  ⚠️  impact.md 不存在（建议先运行 impact.py）")
        print(f"       运行：python3 governance/impact.py {project_dir.name} {ch_id}")
        if not confirm("  未运行 impact.py，仍要继续 apply 吗？"):
            print("已取消。请先运行 impact.py 评估影响范围。")
            sys.exit(0)
    else:
        print(f"  ✅ impact.md 已存在")

    # 汇总检查结果
    print()
    print(f"📋 变更摘要：")
    print(f"   ID：{ch_id}")
    # 提取标题
    for line in read_file(proposal_path).splitlines():
        if line.startswith("# "):
            print(f"   标题：{line[2:].strip()}")
            break
    print(f"   目录：{change_dir}")
    print()

    # 交互确认
    if not confirm("是否确认开始实施此变更？"):
        print("已取消。")
        sys.exit(0)

    # 更新状态
    if update_status_in_proposal(proposal_path, "in-progress"):
        print()
        print(f"✅ 已将 {ch_id} 状态更新为 in-progress")
        print()
        print("下一步：")
        print("  1. 按照 delta.md 中的变更范围开始实施")
        print("  2. 实施过程中 git commit 会自动触发 arch-check + lock-check")
        print(f"  3. 实施完成后：python3 governance/apply-and-archive.py {project_dir.name} {ch_id} archive")
    else:
        print(f"⚠️  状态更新失败，请手动将 proposal.md 中「当前状态」改为 in-progress")


# ---------------------------------------------------------------------------
# archive 阶段
# ---------------------------------------------------------------------------

def do_archive(project_dir: Path, ch_id: str) -> None:
    """执行 archive 操作：in-progress → archived，移动到 archive/ 目录。"""
    change_dir = project_dir / "changes" / "active" / ch_id
    proposal_path = change_dir / "proposal.md"

    print(f"📦 归档变更 {ch_id}...\n")

    # 检查目录存在
    if not change_dir.exists():
        print(f"❌ 变更目录不存在: {change_dir}")
        print(f"   如果变更已在 archive/ 中，无需再次归档")
        sys.exit(1)

    if not proposal_path.exists():
        print(f"❌ proposal.md 不存在: {proposal_path}")
        sys.exit(1)

    # 检查 1：状态必须是 in-progress
    current_status = get_current_status(proposal_path)
    if current_status == "draft":
        print(f"⚠️  变更仍处于 draft 状态，请先执行 apply 操作：")
        print(f"   python3 governance/apply-and-archive.py {project_dir.name} {ch_id} apply")
        sys.exit(1)
    if current_status == "archived":
        print(f"⚠️  变更已归档，无需再次操作")
        sys.exit(0)
    print(f"  ✅ 当前状态：{current_status}")

    # 检查 2：扫描未完成任务（从 TASKS.md 或当前 Sprint 中查找）
    tasks_files = list(change_dir.glob("*.md")) + list(
        (project_dir / "sprints").glob("**/TASKS.md") if (project_dir / "sprints").exists() else []
    )
    total_incomplete = 0
    for tasks_file in tasks_files:
        if "TASKS" in tasks_file.name.upper():
            content = read_file(tasks_file)
            incomplete = count_incomplete_tasks(content)
            if incomplete > 0:
                total_incomplete += incomplete
                print(f"  ⚠️  {tasks_file.name} 中有 {incomplete} 个未完成任务")

    if total_incomplete > 0:
        print()
        print(f"  ⚠️  共发现 {total_incomplete} 个未完成任务")
        if not confirm("  仍有未完成任务，确认归档吗？"):
            print("已取消。请先完成所有任务后再归档。")
            sys.exit(0)
    else:
        print(f"  ✅ 未发现未完成任务")

    # 提取变更标题（用于 changelog）
    ch_title = ch_id
    for line in read_file(proposal_path).splitlines():
        if line.startswith("# "):
            title_raw = line[2:].strip()
            # 去掉 CH-NNN: 前缀
            m = re.match(r"CH-\d+[：:]\s*(.+)", title_raw)
            ch_title = m.group(1) if m else title_raw
            break

    # 汇总
    print()
    print(f"📋 归档摘要：")
    print(f"   ID：{ch_id}")
    print(f"   标题：{ch_title}")
    print(f"   源目录：{change_dir}")
    target_dir = project_dir / "changes" / "archive" / ch_id
    print(f"   目标目录：{target_dir}")
    print()

    # 交互确认
    if not confirm("是否确认归档此变更？"):
        print("已取消。")
        sys.exit(0)

    # 更新状态为 archived
    update_status_in_proposal(proposal_path, "archived")

    # 移动到 archive/ 目录
    archive_base = project_dir / "changes" / "archive"
    archive_base.mkdir(parents=True, exist_ok=True)

    if target_dir.exists():
        print(f"⚠️  目标目录已存在，将覆盖：{target_dir}")
        shutil.rmtree(target_dir)

    shutil.move(str(change_dir), str(target_dir))
    print(f"✅ 变更目录已移动：{change_dir} → {target_dir}")

    # 追加 RFC_CHANGELOG.md
    changelog_path = project_dir / "RFC_CHANGELOG.md"
    append_to_changelog(changelog_path, ch_id, ch_title, project_dir.name)
    print(f"✅ RFC_CHANGELOG.md 已追加记录")

    print()
    print("=" * 60)
    print("📌 归档完成！请执行以下手动步骤：")
    print("=" * 60)
    print()
    print(f"  1. 将 delta.md 中的变更合并回 RFC.md")
    print(f"     delta.md 位置：{target_dir}/delta.md")
    print(f"     RFC.md 位置：{project_dir}/RFC.md")
    print()
    print(f"  2. 更新 RFC.md 中对应 REQ 条目的「状态」字段：")
    print(f"     - 新增的需求：draft → approved → implemented")
    print(f"     - 修改的需求：更新描述内容")
    print(f"     - 删除的需求：状态改为 deprecated")
    print()
    print(f"  3. 更新 RFC_CHANGELOG.md 中刚追加条目的缺失字段：")
    print(f"     - 实施 Sprint")
    print(f"     - 涉及需求")
    print(f"     - 实施结果")
    print(f"     - 归档人")
    print()
    print(f"  4. 如果有锁定文件可以解锁，更新 LOCK.md")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 4:
        print("用法：python3 governance/apply-and-archive.py <project-id> <ch-id> <apply|archive>")
        print()
        print("示例：")
        print("  python3 governance/apply-and-archive.py project-001 CH-001 apply")
        print("  python3 governance/apply-and-archive.py project-001 CH-001 archive")
        sys.exit(1)

    project_id = sys.argv[1]
    ch_id = sys.argv[2].upper()
    action = sys.argv[3].lower()

    if not ch_id.startswith("CH-"):
        ch_id = f"CH-{ch_id}"

    if action not in ("apply", "archive"):
        print(f"❌ 未知操作：{action}（只支持 apply 或 archive）")
        sys.exit(1)

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    project_dir = project_root / "specs" / project_id

    if not project_dir.exists():
        print(f"❌ 项目目录不存在: {project_dir}")
        sys.exit(1)

    if action == "apply":
        do_apply(project_dir, ch_id)
    else:
        do_archive(project_dir, ch_id)


if __name__ == "__main__":
    main()
