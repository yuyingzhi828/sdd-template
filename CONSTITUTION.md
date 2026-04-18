# CONSTITUTION.md — 项目宪法

> **说明**：本文件是项目的最高约束文档。所有开发决策（人工或 AI）必须遵守此处的规则。  
> 使用本模板时，将所有 `<占位符>` 替换为项目实际内容。  
> 本文件一旦确定，修改需要所有核心成员（或项目 owner）明确批准。

---

## 项目简介

> **一句话描述项目是什么，解决什么问题。**

```
<项目名称>：<一句话描述，例：面向中小团队的内容发布管理系统，支持多平台一键分发>
```

---

## 技术栈约束

> **列出所有技术栈，并写明版本要求。AI 生成代码时必须遵守。**

```yaml
# 运行时
language: Python 3.11+          # 示例：不允许使用 3.10 以下特性
runtime: <填写实际运行时>

# Web 框架
framework: <例：FastAPI 0.100+>
asgi_server: <例：uvicorn>

# 数据库
primary_db: <例：PostgreSQL 15>
cache: <例：Redis 7>
orm: <例：SQLAlchemy 2.0（async）>

# 任务队列
task_queue: <例：Celery + Redis | 无>

# 前端（如有）
frontend: <例：React 18 + TypeScript 5 | 无>

# 测试
test_framework: pytest
coverage_threshold: 80%

# 其他
container: Docker + docker-compose
ci: <例：GitHub Actions | 无>
```

> ⚠️ **新增技术依赖** 必须在此处先登记，再使用。AI 不得擅自引入未列出的依赖。

---

## 架构红线

> **这些是硬性禁止事项。违反任意一条视为严重问题，`arch-check.py` 会自动检测部分规则。**

### 分层架构规则

```
API 层 (api/)
  └── 可调用：services/, models/
  └── 禁止：直接写业务逻辑，直接操作数据库

Services 层 (services/)
  └── 可调用：models/, utils/
  └── 禁止：import api/ 中的任何模块

Models 层 (models/)
  └── 可调用：无其他应用层
  └── 禁止：import api/, services/

Tasks 层 (tasks/)
  └── 可调用：services/, models/
  └── 禁止：import api/
```

### 通用红线

- **禁止循环依赖**：模块 A import 模块 B，模块 B 不得再 import 模块 A
- **禁止在 API 层写业务逻辑**：route handler 只做参数校验 + 调用 service + 返回响应
- **禁止在 Model 层写业务逻辑**：Model 只描述数据结构和基础关系
- **禁止硬编码配置**：所有配置通过环境变量或配置文件注入，不得写死在代码里
- **禁止直接修改 migration 历史**：只能新增 migration，不能修改或删除已提交的 migration
- **禁止在非测试代码中使用 `print()`**：日志统一用 `logging` 模块

### 自定义红线

> **在此添加项目特有的约束**

```
- <例：禁止在同一个 HTTP 请求中发起超过 3 次数据库查询，复杂查询必须走 service 层聚合>
- <例：所有外部 API 调用必须有超时设置（默认 10s）>
- <例：禁止在 service 层直接返回 ORM 对象，必须转换为 Pydantic schema>
```

---

## 反模式约束（Anti-Patterns）

> **这是喂给 AI 最有效的约束层。告诉 AI「绝对不能做什么」，比告诉它「该做什么」更重要。**  
> **`arch-check.py` 会检测部分规则，其余在 Code Review 阶段人工核查。**

### 代码质量禁令

```
❌ 禁止硬编码（Magic Numbers / Magic Strings）
   → 所有配置值、枚举值必须提取到配置文件或常量模块，不得写死在业务代码中

❌ 禁止吞没异常（Silent Exception Swallowing）
   → 空的 catch/except 块一律禁止
   → 所有异常必须：记录日志（logging）+ 抛出合适的错误码或重新 raise

❌ 禁止面条代码（Spaghetti Code）
   → 单个函数超过 50 行必须拆分为具备独立职责的子函数
   → 单个文件超过 500 行必须拆分为子模块
   → 嵌套层级不超过 4 层

❌ 禁止引入未授权依赖
   → 除非在 CONSTITUTION.md「技术栈约束」中已列出，否则不得引入任何新的第三方库
   → 新增依赖必须先更新 CONSTITUTION.md，经人工审批后再使用

❌ 禁止过度设计（Over-engineering）
   → 只实现当前 RFC.md 和 TK-NNN.md 中明确定义的功能
   → Out of scope 的内容绝对不实现，哪怕"顺手"也不行

❌ 禁止私自修改已锁定的数据模型字段
   → 数据库 Schema 变更必须走 propose → delta → apply 变更流程
   → 已锁定文件（见 LOCK.md）的修改需要解锁申请
```

### AI 专项禁令

> **以下约束专门针对 AI 生成代码的常见问题**

```
❌ 禁止生成"占位符逻辑"（pass / TODO / raise NotImplementedError）混入生产代码
   → 如果 AI 无法完成某段逻辑，必须明确说明，不得用占位符蒙混

❌ 禁止在没有测试的情况下完成任务
   → 每个 TK 的核心业务逻辑必须附带单元测试
   → 测试覆盖率不低于 80%

❌ 禁止一次性提交超出 TK 范围的文件
   → AI 每次只能修改 TK-NNN.md「允许修改的文件范围」中列出的文件
   → 超出范围的修改视为越权，需打回重做

❌ 禁止在未阅读以下文件的情况下开始写代码
   必读清单：CONSTITUTION.md → RFC.md → LOCK.md → TK-NNN.md
```

---

## AI 使用约定

> **每次让 AI 开始任务前，必须明确告知以下约定。**

### AI 能做的事

- 在 `TK-NNN.md` **允许修改的文件范围** 内生成/修改代码
- 编写单元测试
- 重构已授权范围内的代码
- 解释代码逻辑
- 根据 RFC.md 需求生成初步实现

### AI 不能做的事

- **不能修改 LOCK.md 中锁定的文件**（会被 `lock-check.py` 阻断）
- **不能引入未在 CONSTITUTION.md 技术栈中列出的依赖**
- **不能修改数据库 migration 历史**
- **不能修改 `CONSTITUTION.md` 本身**（需人工审批）
- **不能自行决定变更 RFC.md 需求**（需走 propose → delta 流程）

### AI 每次任务开始前必读文件

```
1. CONSTITUTION.md           ← 本文件
2. specs/{project-id}/RFC.md ← 了解需求全貌
3. specs/{project-id}/LOCK.md ← 了解哪些文件不能碰
4. tasks/TK-NNN.md           ← 了解本次任务范围和验收标准
```

### AI 生成代码的质量要求

- 每个函数必须有 docstring（一行描述即可）
- 关键业务逻辑必须有注释说明「为什么」，不只是「是什么」
- 新增功能必须同时提供测试用例框架（哪怕是空测试）
- 不得生成超过 200 行的单一函数

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
- 禁止使用裸 Any，必须用 TypeVar 或具体类型

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
格式：<type>(<scope>): <subject>

type:
  feat     - 新功能
  fix      - Bug 修复
  refactor - 重构（不改功能）
  test     - 测试相关
  docs     - 文档修改
  chore    - 构建/工具链

示例：
  feat(user): add email verification on registration
  fix(api): return 409 when duplicate email detected
  docs(constitution): add AI usage constraints
```

---

## 变更记录

> **本文件的修改历史（手动维护）**

| 日期 | 修改人 | 修改内容 |
|------|--------|---------|
| YYYY-MM-DD | <姓名> | 初始化 |
