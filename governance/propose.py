#!/usr/bin/env python3
"""
propose.py — 生成变更提案（CH-NNN）

用法：
    python3 governance/propose.py <project-id> "<变更标题>" [--description "自然语言描述"]

示例：
    python3 governance/propose.py project-001 "添加用户导出功能"
    python3 governance/propose.py project-001 "添加用户导出功能" --description "需要支持将用户数据导出为 CSV 格式"

功能：
    1. 扫描 active/ 和 archive/ 目录，自动分配下一个 CH-NNN 编号
    2. 在 active/CH-NNN/ 下生成 proposal.md 和 delta.md
    3. 如果提供了 --description，调用 AI 生成初稿（当前为占位符实现）
    4. 输出生成的文件路径
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# AI 调用占位符
# ---------------------------------------------------------------------------

def call_ai(prompt: str) -> str:
    """
    TODO: 替换为实际 AI 调用。

    支持的后端：
    - Claude API: pip install anthropic; 设置 ANTHROPIC_API_KEY
      示例：
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(model="claude-opus-4-5", max_tokens=2048,
                                     messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text

    - OpenAI: pip install openai; 设置 OPENAI_API_KEY
      示例：
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(model="gpt-4o",
                   messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content

    - Ollama (本地): pip install ollama; 本地运行 ollama serve
      示例：
        import ollama
        resp = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
        return resp["message"]["content"]

    当前返回占位符内容，实际使用时替换此函数体。
    """
    return f"[AI 生成内容占位符]\n\n基于描述：{prompt}\n\n请手动填写实际内容。"


# ---------------------------------------------------------------------------
# 编号分配
# ---------------------------------------------------------------------------

def get_next_ch_id(project_dir: Path) -> str:
    """扫描 active/ 和 archive/ 目录，返回下一个可用的 CH-NNN 编号。"""
    active_dir = project_dir / "changes" / "active"
    archive_dir = project_dir / "changes" / "archive"

    max_num = 0
    pattern = re.compile(r"^CH-(\d+)$", re.IGNORECASE)

    for directory in [active_dir, archive_dir]:
        if not directory.exists():
            continue
        for entry in directory.iterdir():
            if entry.is_dir():
                m = pattern.match(entry.name)
                if m:
                    num = int(m.group(1))
                    max_num = max(max_num, num)

    next_num = max_num + 1
    return f"CH-{next_num:03d}"


# ---------------------------------------------------------------------------
# 文件生成
# ---------------------------------------------------------------------------

def generate_proposal(ch_id: str, title: str, description: str | None, today: str) -> str:
    """生成 proposal.md 内容。"""
    if description:
        ai_context = call_ai(
            f"为以下变更生成一份详细的变更提案（Proposal）：\n"
            f"变更标题：{title}\n"
            f"描述：{description}\n"
            f"请填写：背景、变更范围、预期收益、不在范围内的内容、风险。"
        )
        background_section = ai_context
    else:
        background_section = "> 请填写：为什么要做这个变更？当前痛点是什么？"

    return f"""# {ch_id}: {title}

## 状态

- **提议时间**：{today}
- **当前状态**：draft
- **变更 ID**：{ch_id}
- **提议人**：<填写提议人姓名>

---

## 背景

{background_section}

---

## 变更范围

> 这次变更涉及哪些功能模块、哪些文件

**功能模块**：
- `<模块名>`：<具体变更内容>

**预期涉及文件**：
- `<文件路径>` — <为什么要改>

---

## 预期收益

> 这个变更完成后，用户/系统获得什么

- **用户侧**：<描述>
- **系统侧**：<描述>

---

## 不在范围内

> 明确排除的内容，防止范围蔓延

- ❌ <明确不做的事 1>
- ❌ <明确不做的事 2>

---

## 风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| <风险描述> | 低/中/高 | 低/中/高 | <缓解措施> |

---

## 关联文档

- **对应 Delta**：`{ch_id}/delta.md`
- **影响评估**：`{ch_id}/impact.md`（运行 impact.py 后生成）
"""


def generate_delta(ch_id: str, title: str, description: str | None, today: str) -> str:
    """生成 delta.md 内容。"""
    if description:
        ai_context = call_ai(
            f"为以下变更生成一份 RFC Delta 文档，描述对 RFC.md 的具体增删改：\n"
            f"变更标题：{title}\n"
            f"描述：{description}\n"
            f"请按格式列出：新增需求（ADD REQ-NNN）、修改需求（MODIFY REQ-NNN）、删除需求（DELETE REQ-NNN）。"
        )
        changes_section = ai_context
    else:
        changes_section = "> 请填写对 RFC.md 的具体变更内容（REQ 级别的增删改）"

    return f"""# {ch_id} Delta

> **说明**：本文件描述对 RFC.md 的精确变更。
> 填写完毕后运行 `python3 governance/impact.py <project-id> {ch_id}` 分析影响范围。
> 归档后，需手动将这里的变更合并回 RFC.md。
>
> 机器可读标记格式：
> <!-- [ACTION] REQ-ID: 说明 -->
> ACTION 可选值：ADD | MODIFY | DELETE

---

## 对 RFC.md 的变更

{changes_section}

### 新增需求

<!-- [ADD] REQ-NNN: <需求描述> -->

```markdown
### REQ-NNN: <需求标题>

- **描述**：<详细描述>
- **验收标准**：
  - <条件 1>
- **优先级**：P0 / P1 / P2
- **状态**：draft
- **关联**：<关联需求编号>
```

---

### 修改需求

<!-- [MODIFY] REQ-NNN: 原文 → 新文 -->

| 字段 | 原文 | 新文 |
|------|------|------|
| <字段名> | <原内容> | <新内容> |

---

### 删除需求

<!-- [DELETE] REQ-NNN: 删除原因 -->

> （无删除需求则保留此提示）

---

## 涉及的锁定文件

> 对照 LOCK.md 填写，impact.py 也会自动分析

| 文件 | 是否锁定 | 锁定所属 Sprint | 需要解锁申请 |
|-----|---------|--------------|-----------|
| `<文件路径>` | ❌ 否 | - | 否 |

---

## 数据库变更（如有）

```sql
-- 在此填写 DDL 变更语句
```

---

## API 变更（如有）

| 操作 | 方法 | 路径 | 变更类型 |
|------|------|------|---------|
| <新增/修改/删除> | GET/POST/PUT/DELETE | `/api/v1/...` | 新接口/参数变更/废弃 |
"""


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="生成 SDD 变更提案（CH-NNN）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 governance/propose.py project-001 "添加用户导出功能"
  python3 governance/propose.py project-001 "添加用户导出功能" --description "需要支持 CSV 导出"
        """,
    )
    parser.add_argument("project_id", help="项目 ID，如 project-001")
    parser.add_argument("change_title", help="变更标题，用引号包裹")
    parser.add_argument("--description", "-d", default=None, help="变更的自然语言描述，用于 AI 生成初稿")
    args = parser.parse_args()

    # 定位 specs 目录（相对于脚本所在目录的上一级）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    specs_dir = project_root / "specs"
    project_dir = specs_dir / args.project_id

    if not project_dir.exists():
        print(f"❌ 项目目录不存在: {project_dir}")
        print(f"   请先创建目录并初始化 RFC.md / LOCK.md")
        sys.exit(1)

    # 分配编号
    ch_id = get_next_ch_id(project_dir)
    today = date.today().isoformat()

    # 创建变更目录
    change_dir = project_dir / "changes" / "active" / ch_id
    change_dir.mkdir(parents=True, exist_ok=True)

    # 生成 proposal.md
    proposal_path = change_dir / "proposal.md"
    proposal_content = generate_proposal(ch_id, args.change_title, args.description, today)
    proposal_path.write_text(proposal_content, encoding="utf-8")

    # 生成 delta.md
    delta_path = change_dir / "delta.md"
    delta_content = generate_delta(ch_id, args.change_title, args.description, today)
    delta_path.write_text(delta_content, encoding="utf-8")

    # 输出结果
    print(f"✅ 变更提案已生成：{ch_id}")
    print(f"   标题：{args.change_title}")
    print(f"   目录：{change_dir}")
    print()
    print(f"   📄 {proposal_path}")
    print(f"   📄 {delta_path}")
    print()
    print("下一步：")
    print(f"  1. 编辑 delta.md，填写对 RFC.md 的具体增删改")
    print(f"  2. 运行：python3 governance/impact.py {args.project_id} {ch_id}")
    print(f"  3. 确认影响范围后：python3 governance/apply-and-archive.py {args.project_id} {ch_id} apply")


if __name__ == "__main__":
    main()
