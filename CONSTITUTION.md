# CONSTITUTION.md — 项目宪法

> **说明**:本文件是项目的最高约束文档。所有开发决策(人工或 AI)必须遵守此处的规则。
> 使用本模板时,将所有 `<占位符>` 替换为项目实际内容。
> 本文件一旦确定,修改需要所有核心成员(或项目 owner)明确批准。

---

## 项目简介

> **一句话描述项目是什么,解决什么问题。**

```
<项目名称>:<一句话描述,例:面向中小团队的内容发布管理系统,支持多平台一键分发>
```

---

## 元基础设施定义

> **"元基础设施"是一类特殊的文件——它们不是某个具体项目的内容,而是"模板本身"的构成部分。
> 对它们的修改会级联影响所有基于本模板的下游项目。因此治理规则格外严格。**

以下路径下的文件/目录属于元基础设施:

- `governance/` 下的所有脚本(`propose.py` / `impact.py` / `apply-and-archive.py` / `arch-check.py` / `lock-check.py` / `pre-commit.sh` 等)
- `templates/` 下的所有模板文件(`*.template.md`)
- `CONSTITUTION.md` 本身
- 根目录的 `AGENTS.md` / `CLAUDE.md` / `SKILL.md`(如有)

**识别标志**:如果一次修改会影响"未来某个尚不存在的项目怎么初始化",它改的就是元基础设施。

对元基础设施的修改必须遵守下文「元基础设施变更规则」。

---

## 技术栈约束

> **列出所有技术栈,并写明版本要求。AI 生成代码时必须遵守。**

```yaml
# 运行时
language: Python 3.11+          # 示例:不允许使用 3.10 以下特性
runtime: <填写实际运行时>

# Web 框架
framework: <例:FastAPI 0.100+>
asgi_server: <例:uvicorn>

# 数据库
primary_db: <例:PostgreSQL 15>
cache: <例:Redis 7>
orm: <例:SQLAlchemy 2.0(async)>

# 任务队列
task_queue: <例:Celery + Redis | 无>

# 前端(如有)
frontend: <例:React 18 + TypeScript 5 | 无>

# 测试
test_framework: pytest
coverage_threshold: 80%

# 其他
container: Docker + docker-compose
ci: <例:GitHub Actions | 无>
```

> ⚠️ **新增技术依赖** 必须在此处先登记,再使用。AI 不得擅自引入未列出的依赖。

---

## 架构红线

> **这些是硬性禁止事项。违反任意一条视为严重问题,`arch-check.py` 会自动检测部分规则。**

### 分层架构规则

```
API 层 (api/)
  └── 可调用:services/, models/
  └── 禁止:直接写业务逻辑,直接操作数据库

Services 层 (services/)
  └── 可调用:models/, utils/
  └── 禁止:import api/ 中的任何模块

Models 层 (models/)
  └── 可调用:无其他应用层
  └── 禁止:import api/, services/

Tasks 层 (tasks/)
  └── 可调用:services/, models/
  └── 禁止:import api/
```

### 通用红线

- **禁止循环依赖**:模块 A import 模块 B,模块 B 不得再 import 模块 A
- **禁止在 API 层写业务逻辑**:route handler 只做参数校验 + 调用 service + 返回响应
- **禁止在 Model 层写业务逻辑**:Model 只描述数据结构和基础关系
- **禁止硬编码配置**:所有配置通过环境变量或配置文件注入,不得写死在代码里
- **禁止直接修改 migration 历史**:只能新增 migration,不能修改或删除已提交的 migration
- **禁止在非测试代码中使用 `print()`**:日志统一用 `logging` 模块

### 自定义红线

> **在此添加项目特有的约束**

```
- <例:禁止在同一个 HTTP 请求中发起超过 3 次数据库查询,复杂查询必须走 service 层聚合>
- <例:所有外部 API 调用必须有超时设置(默认 10s)>
- <例:禁止在 service 层直接返回 ORM 对象,必须转换为 Pydantic schema>
```

---

## 反模式约束(Anti-Patterns)

> **这是喂给 AI 最有效的约束层。告诉 AI「绝对不能做什么」,比告诉它「该做什么」更重要。**
> **`arch-check.py` 会检测部分规则,其余在 Code Review 阶段人工核查。**

### 代码质量禁令

```
❌ 禁止硬编码(Magic Numbers / Magic Strings)
   → 所有配置值、枚举值必须提取到配置文件或常量模块,不得写死在业务代码中

❌ 禁止吞没异常(Silent Exception Swallowing)
   → 空的 catch/except 块一律禁止
   → 所有异常必须:记录日志(logging)+ 抛出合适的错误码或重新 raise

❌ 禁止面条代码(Spaghetti Code)
   → 单个函数超过 50 行必须拆分为具备独立职责的子函数
   → 单个文件超过 500 行必须拆分为子模块
   → 嵌套层级不超过 4 层

❌ 禁止引入未授权依赖
   → 除非在 CONSTITUTION.md「技术栈约束」中已列出,否则不得引入任何新的第三方库
   → 新增依赖必须先更新 CONSTITUTION.md,经人工审批后再使用

❌ 禁止过度设计(Over-engineering)
   → 只实现当前 RFC.md 和 TK-NNN.md 中明确定义的功能
   → Out of scope 的内容绝对不实现,哪怕"顺手"也不行

❌ 禁止私自修改已锁定的数据模型字段
   → 数据库 Schema 变更必须走 propose → delta → apply 变更流程
   → 已锁定文件(见 LOCK.md)的修改需要解锁申请
```

### AI 专项禁令

> **以下约束专门针对 AI 生成代码的常见问题**

```
❌ 禁止生成"占位符逻辑"(pass / TODO / raise NotImplementedError)混入生产代码
   → 如果 AI 无法完成某段逻辑,必须明确说明,不得用占位符蒙混

❌ 禁止在没有测试的情况下完成任务
   → 每个 TK 的核心业务逻辑必须附带单元测试
   → 测试覆盖率不低于 80%

❌ 禁止一次性提交超出 TK 范围的文件
   → AI 每次只能修改 TK-NNN.md「允许修改的文件范围」中列出的文件
   → 超出范围的修改视为越权,需打回重做

❌ 禁止在未阅读以下文件的情况下开始写代码
   必读清单:CONSTITUTION.md → RFC.md → LOCK.md → TK-NNN.md
```

---

## AI 使用约定

> **每次让 AI 开始任务前,必须明确告知以下约定。**

### AI 能做的事

- 在 `TK-NNN.md` **允许修改的文件范围** 内生成/修改代码
- 编写单元测试
- 重构已授权范围内的代码
- 解释代码逻辑
- 根据 RFC.md 需求生成初步实现

### AI 不能做的事

- **不能修改 LOCK.md 中锁定的文件**(会被 `lock-check.py` 阻断)
- **不能引入未在 CONSTITUTION.md 技术栈中列出的依赖**
- **不能修改数据库 migration 历史**
- **不能修改 `CONSTITUTION.md` 本身**(需人工审批)
- **不能自行决定变更 RFC.md 需求**(需走 propose → delta 流程)
- **不能擅自修改元基础设施**(详见「元基础设施变更规则」)
- **不能替用户回答交互式提示**(如 `y/n` 确认、脚本中途询问)
- **不能伪造或自行批准审批记录**(如在 LOCK.md 的解锁表追加"已批准")

### AI 必须做的事(流程纪律)

> **以下规则专门针对 AI 常见的"超前越界"倾向——即便是出于好意、出于效率,也必须遵守。**

- **严格遵守用户的分步指令**:如果用户说"写完 X 让我看一眼再继续",即便下一步再明显,也必须停下来等用户确认。**不得合并多步一次性完成**
- **修改任何文件前,必须先确认该文件的 LOCK 状态**:读 LOCK.md,确认不在锁定列表中,或已有对应的解锁批准
- **执行任何脚本前,必须先用 `-h` 或阅读源码确认参数**:不得凭猜测传参
- **遇到工具/脚本报错时,必须如实完整汇报错误信息**:不得擅自修复、绕过或隐瞒
- **发现模板/脚本/配置之间存在不一致时,必须先报告,由人类决策如何处理**:AI 不得自行修复元基础设施
- **不确定时必须停下来问**:不得凭"大概意思"推进。宁可多问一轮,也不要猜错一次
- **每一步完成后必须汇报当前状态**:特别是涉及文件修改、git commit、脚本执行时

### AI 每次任务开始前必读文件

```
1. CONSTITUTION.md           ← 本文件
2. specs/{project-id}/RFC.md ← 了解需求全貌
3. specs/{project-id}/LOCK.md ← 了解哪些文件不能碰
4. tasks/TK-NNN.md           ← 了解本次任务范围和验收标准
```

### AI 生成代码的质量要求

- 每个函数必须有 docstring(一行描述即可)
- 关键业务逻辑必须有注释说明「为什么」,不只是「是什么」
- 新增功能必须同时提供测试用例框架(哪怕是空测试)
- 不得生成超过 200 行的单一函数

---

## 元基础设施变更规则

> **元基础设施的特性是:一次修改,影响所有下游项目。因此变更流程比普通功能更严格。**

### 为什么单独立规

想象这样一种情境:某个 AI 助手在处理一个具体项目时,觉得 `templates/delta.template.md` 的语法"太复杂",随手把它简化了一下。这个改动:

1. **在当时看不出问题**——当前项目的 CH 依然能创建、能归档(因为 AI 脑子里的简化语法和它自己写出来的 delta 是一致的)
2. **不会触发 `lock-check.py`**(如果 `templates/` 没被锁定)
3. **但所有未来基于这个仓库初始化的项目,都会继承这个错误**
4. **等到你某天想归档一个 CH,发现 `apply-and-archive.py` 跑不通时,已经过去几周了**,你根本想不起来谁在什么时候改了什么

**这就是为什么元基础设施的变更,哪怕"看起来是改进",也必须走慢流程。**

### 元基础设施变更的六步流程

1. **发起 CH 提议**——不能直接改文件,必须先开 CH
2. **CH 命名使用 `CH-META-xxx` 前缀**——例如 `CH-META-001-refactor-delta-syntax`,与业务 CH 区别开
3. **proposal.md 必须明确回答三件事**:
   - 这次修改影响哪些下游项目(已存在的 + 未来新建的)
   - 是否需要为已存在的下游项目做迁移工作
   - 如果事后发现问题,如何回滚
4. **impact.py 分析必须覆盖"跨项目影响"**——不只是当前项目
5. **人类审批是硬要求,AI 不得作为审批人**——批准人必须是人类 owner
6. **合并后必须在测试项目中验证**——至少新建一个测试项目走一遍完整流程,确认元基础设施没坏

### 推荐:把元基础设施加入 LOCK.md

在 `LOCK.md` 中显式登记元基础设施文件,例如:

```
[LOCK-META-001] governance/propose.py
[LOCK-META-002] governance/impact.py
[LOCK-META-003] governance/apply-and-archive.py
[LOCK-META-004] templates/delta.template.md
[LOCK-META-005] templates/proposal.template.md
[LOCK-META-006] CONSTITUTION.md
```

这样 `lock-check.py` 会在 pre-commit 阶段自动拦截对这些文件的直接修改,强制走 CH-META 流程。

---

## 代码风格约定

> **格式化和代码风格规则。可与 linter 配置对应。**

### Python

```python
# 格式化工具
formatter: black (line-length=100)
linter: ruff
type_checker: mypy (strict mode for core modules)

# 命名约定
变量/函数: snake_case
类名: PascalCase
常量: UPPER_SNAKE_CASE
私有方法: _leading_underscore

# 类型注解
- 所有 public 函数必须有完整类型注解
- 禁止使用裸 Any,必须用 TypeVar 或具体类型

# 导入排序
- 标准库 → 第三方 → 本项目内部
- 使用 isort 或 ruff 自动排序
```

### 文件组织

```
# 单个文件不超过 500 行
# 超过时拆分为子模块

# 测试文件与源文件对应
src/services/user.py → tests/services/test_user.py
```

### Git 提交规范

```
格式:<type>(<scope>): <subject>

type:
  feat     - 新功能
  fix      - Bug 修复
  refactor - 重构(不改功能)
  test     - 测试相关
  docs     - 文档修改
  chore    - 构建/工具链
  meta     - 元基础设施修改(必须对应 CH-META-xxx)

示例:
  feat(user): add email verification on registration
  fix(api): return 409 when duplicate email detected
  docs(constitution): add AI usage constraints
  meta(template): fix delta template OP block syntax (CH-META-003)
```

---

## 变更记录

> **本文件的修改历史(手动维护)**

| 日期 | 修改人 | 修改内容 |
|------|--------|---------|
| YYYY-MM-DD | <姓名> | 初始化 |
| YYYY-MM-DD | <姓名> | 新增「元基础设施定义」「AI 必须做的事」「元基础设施变更规则」三节(CH-META-001) |
