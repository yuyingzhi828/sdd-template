# SDD 通用项目模板

**Spec-Driven Development（规格驱动开发）** 模板仓库。  
把「写什么、怎么验收、谁能改什么」全部变成可追踪、可检查的文件，让 AI 辅助开发有据可查、不失控。

---

## 这套模板解决什么问题

| 痛点 | 解法 |
|------|------|
| AI 改了不该改的文件 | `LOCK.md` + `lock-check.py` 在提交时阻断 |
| 需求在聊天记录里，找不到 | `RFC.md` 是唯一需求源，带编号 + 状态 |
| 变更范围不断蔓延 | `propose.py` 强制每次变更先写 proposal，明确 scope |
| 不知道哪个模块影响了哪个 | `impact.py` 自动扫描依赖，给出风险等级 |
| 架构约束靠口头约定 | `CONSTITUTION.md` + `arch-check.py` 在提交时强制校验 |

---

## 目录结构与职责

```
sdd-template/
├── README.md                   # 本文件，使用说明
├── CONSTITUTION.md             # 项目宪法：技术栈、架构红线、AI 使用约定
├── specs/
│   └── project-000-template/  # 每个项目/子系统一个目录
│       ├── RFC.md              # 需求规格：唯一需求源，REQ-NNN 编号
│       ├── PLAN.md             # 实施计划：Sprint 列表、里程碑
│       ├── LOCK.md             # 锁定清单：哪些文件已锁、如何申请解锁
│       ├── RFC_CHANGELOG.md    # 需求变更历史：每次 archive 后追加
│       ├── changes/
│       │   ├── active/         # 进行中的变更提案 (CH-NNN/)
│       │   └── archive/        # 已归档的变更提案
│       └── sprints/
│           └── sprint-001-template/
│               ├── TASKS.md    # Sprint 任务清单 + 完成标准
│               ├── REVIEWS.md  # Sprint 回顾记录
│               └── tasks/
│                   └── TK-001-template.md  # 单个任务卡片
├── governance/
│   ├── propose.py              # 生成变更提案（CH-NNN）
│   ├── impact.py               # 评估变更影响范围
│   ├── apply-and-archive.py    # 推进变更状态（draft→in-progress→archive）
│   ├── arch-check.py           # 架构分层合规检查
│   ├── lock-check.py           # 锁定文件保护检查
│   └── pre-commit.sh           # Git pre-commit hook，串联所有检查
└── tests/
    └── .gitkeep                # 测试目录占位
```

---

## 新项目快速上手

### 第一步：复制模板

```bash
cp -r sdd-template/ my-new-project/
cd my-new-project/
git init
```

### 第二步：初始化 CONSTITUTION

编辑 `CONSTITUTION.md`，填写：
- 项目一句话简介
- 实际技术栈（Python 版本、框架、数据库等）
- 架构红线（禁止事项）
- AI 使用约定（哪些文件 AI 必须先读）

### 第三步：重命名项目规格目录

```bash
mv specs/project-000-template specs/project-001-your-project-name
```

更新目录内 RFC.md、PLAN.md、LOCK.md 中的项目编号引用。

### 第四步：写第一个 RFC

编辑 `specs/project-001-xxx/RFC.md`，按 F1/F2... 功能域划分，  
为每个需求写 `REQ-001`、`REQ-002`... 条目。

### 第五步：安装 pre-commit hook

```bash
cp governance/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 完整变更生命周期

```
需求变化
   │
   ▼
① 提出变更（propose）
   python3 governance/propose.py project-001 "添加用户导出功能" --description "需要支持 CSV 导出"
   → 生成 specs/project-001/changes/active/CH-001/proposal.md + delta.md
   │
   ▼
② 填写 Delta（手动）
   编辑 delta.md，写明对 RFC.md 的具体增删改（REQ-NNN 级别）
   │
   ▼
③ 评估影响（impact）
   python3 governance/impact.py project-001 CH-001
   → 生成 impact.md，标出锁定文件冲突 + 依赖链风险等级
   │
   ▼
④ 确认实施（apply）
   python3 governance/apply-and-archive.py project-001 CH-001 apply
   → 交互确认后，proposal.md 状态改为 in-progress
   │
   ▼
⑤ 实施变更（开发）
   按 TK 任务卡片执行，git commit 时自动触发 arch-check + lock-check
   │
   ▼
⑥ 归档变更（archive）
   python3 governance/apply-and-archive.py project-001 CH-001 archive
   → 移入 archive/，追加 RFC_CHANGELOG.md
   → 提示：手动将 delta.md 内容合并回 RFC.md
```

---

## 脚本速查表

| 脚本 | 示例命令 | 说明 |
|------|---------|------|
| `propose.py` | `python3 governance/propose.py project-001 "新增导出功能" --description "CSV格式导出用户数据"` | 生成变更提案，自动分配 CH-NNN 编号 |
| `impact.py` | `python3 governance/impact.py project-001 CH-001` | 扫描变更影响范围，检查锁定冲突 |
| `apply-and-archive.py` | `python3 governance/apply-and-archive.py project-001 CH-001 apply` | 确认实施，状态 draft→in-progress |
| `arch-check.py` | `python3 governance/arch-check.py` | 检查代码架构分层合规 |
| `lock-check.py` | `git diff --cached --name-only \| python3 governance/lock-check.py` | 检查暂存区是否触碰锁定文件 |

---

## 给 AI 的使用约定

每次让 AI 开始一个任务前，让它先读：
1. `CONSTITUTION.md` — 了解技术栈和红线
2. `specs/{project-id}/RFC.md` — 了解需求全貌
3. `specs/{project-id}/LOCK.md` — 了解哪些文件不能动
4. 对应的 `TK-NNN.md` — 了解本次任务的具体范围

---

## 未来扩展

- 本 README 可直接作为 Cola Skill 的 `SKILL.md` 素材
- `propose.py` 中的 `call_ai()` 函数替换为实际 API 调用后，可自动生成 proposal/delta 初稿
- 可扩展 `arch-check.py` 支持从 `CONSTITUTION.md` 动态读取架构规则（当前已实现）
