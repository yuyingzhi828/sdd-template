#!/usr/bin/env python3
"""
lock-check.py — 锁定文件保护检查（通用版）

用法：
    git diff --cached --name-only | python3 governance/lock-check.py
    echo "src/models/user.py" | python3 governance/lock-check.py
    python3 governance/lock-check.py --files src/models/user.py src/api/auth.py

功能：
    1. 读取 specs/ 下所有项目的 LOCK.md，汇总已锁定文件列表
    2. 对比输入的文件列表（来自 stdin 或 --files 参数）
    3. 如果有文件命中锁定规则，打印警告并以非零退出码退出
    4. 支持精确路径匹配和 glob 模式匹配

设计为 git pre-commit hook 的一部分，在 pre-commit.sh 中被调用。
"""

import fnmatch
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# 解析 LOCK.md
# ---------------------------------------------------------------------------

def get_locked_files_from_lock_md(lock_path: Path) -> list[dict]:
    """
    从单个 LOCK.md 解析已锁定文件表。
    返回列表，每项：{"path": str, "sprint": str, "reason": str, "project": str}
    """
    if not lock_path.exists():
        return []

    locked: list[dict] = []
    in_table = False
    header_found = False
    # 提取项目 ID（从路径中）
    project_id = lock_path.parent.name

    for line in lock_path.read_text(encoding="utf-8").splitlines():
        # 识别「已锁定文件表」的表头行
        if "文件路径" in line and "锁定原因" in line:
            in_table = True
            header_found = True
            continue

        # 跳过分隔行（| --- | --- |）
        if in_table and re.match(r"^\|[-\s|]+\|$", line.strip()):
            continue

        # 解析表格数据行
        if in_table and line.strip().startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 1:
                # 提取文件路径（去掉反引号）
                file_path = cells[0].strip("`").strip()
                # 跳过表头重复行和空行
                if not file_path or file_path == "文件路径" or file_path.startswith("-"):
                    continue
                reason = cells[1].strip() if len(cells) > 1 else ""
                sprint = cells[3].strip() if len(cells) > 3 else ""
                locked.append({
                    "path": file_path,
                    "reason": reason,
                    "sprint": sprint,
                    "project": project_id,
                })
        # 表格结束（遇到非表格行且不是注释）
        elif in_table and header_found and not line.strip().startswith("|"):
            if line.strip() and not line.strip().startswith(">") and not line.strip().startswith("!"):
                in_table = False

    return locked


def collect_all_locked_files(specs_dir: Path) -> list[dict]:
    """扫描 specs/ 下所有项目的 LOCK.md，汇总锁定文件列表。"""
    all_locked: list[dict] = []

    if not specs_dir.exists():
        return all_locked

    for lock_path in specs_dir.glob("*/LOCK.md"):
        locked = get_locked_files_from_lock_md(lock_path)
        all_locked.extend(locked)

    return all_locked


# ---------------------------------------------------------------------------
# 文件匹配
# ---------------------------------------------------------------------------

def match_pattern(filepath: str, pattern: str) -> bool:
    """
    检查 filepath 是否匹配 pattern。
    支持：
    - 精确匹配：src/models/user.py
    - glob 匹配：src/models/*.py
    - 后缀匹配：models/user.py 匹配 src/models/user.py
    """
    # 标准化路径分隔符
    filepath = filepath.replace("\\", "/")
    pattern = pattern.replace("\\", "/")

    # 精确匹配
    if filepath == pattern:
        return True

    # glob 匹配
    if "*" in pattern:
        if fnmatch.fnmatch(filepath, pattern):
            return True
        # 也尝试匹配文件路径的后半段
        if fnmatch.fnmatch(filepath, f"*/{pattern}"):
            return True

    # 后缀路径匹配（pattern 是路径的后半段）
    if filepath.endswith(pattern) or filepath.endswith("/" + pattern):
        return True

    # 前缀路径匹配（filepath 是 pattern 的子路径）
    if pattern.endswith(filepath):
        return True

    return False


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="锁定文件保护检查",
        epilog="示例：git diff --cached --name-only | python3 governance/lock-check.py",
    )
    parser.add_argument(
        "--files", "-f",
        nargs="+",
        default=None,
        help="直接指定要检查的文件列表（不指定则从 stdin 读取）",
    )
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="只检查指定项目的锁定规则（如 project-001），默认检查所有项目",
    )
    args = parser.parse_args()

    # 路径解析
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    specs_dir = project_root / "specs"

    # 收集所有锁定文件
    all_locked = collect_all_locked_files(specs_dir)

    # 按项目过滤
    if args.project:
        all_locked = [e for e in all_locked if e["project"] == args.project]

    if not all_locked:
        print("✅ 无锁定文件规则")
        sys.exit(0)

    # 获取要检查的文件列表
    if args.files:
        staged_files = args.files
    else:
        # 从 stdin 读取（git diff --cached --name-only 的输出）
        if sys.stdin.isatty():
            # 没有管道输入，可能是直接运行
            print("⚠️  没有输入文件列表")
            print("   用法：git diff --cached --name-only | python3 governance/lock-check.py")
            print("   或：  python3 governance/lock-check.py --files <file1> <file2>")
            sys.exit(0)
        staged_files = [line.strip() for line in sys.stdin if line.strip()]

    if not staged_files:
        print("✅ 无暂存文件，跳过锁定检查")
        sys.exit(0)

    # 对比锁定规则
    violations: list[dict] = []
    for filepath in staged_files:
        for lock_entry in all_locked:
            if match_pattern(filepath, lock_entry["path"]):
                violations.append({
                    "file": filepath,
                    "pattern": lock_entry["path"],
                    "sprint": lock_entry["sprint"],
                    "project": lock_entry["project"],
                    "reason": lock_entry["reason"],
                })

    # 输出结果
    if violations:
        print(f"❌ 锁定检查失败：{len(violations)} 个锁定文件被修改")
        print()
        for v in violations:
            print(f"  🔒 {v['file']}")
            print(f"     匹配规则：{v['pattern']}")
            print(f"     项目：{v['project']}")
            if v['sprint']:
                print(f"     锁定 Sprint：{v['sprint']}")
            if v['reason']:
                print(f"     锁定原因：{v['reason']}")
            print()
        print("如需修改锁定文件：")
        print(f"  1. 在 specs/<project-id>/LOCK.md 的「解锁申请表」中登记")
        print(f"  2. 等待审批通过后再提交")
        sys.exit(1)
    else:
        print(f"✅ 锁定检查通过（检查了 {len(staged_files)} 个文件，无冲突）")
        sys.exit(0)


if __name__ == "__main__":
    main()
