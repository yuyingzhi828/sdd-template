# TK-001: <任务标题>

## 基本信息

- **Sprint**：sprint-001
- **优先级**：P0 / P1 / P2
- **预估工时**：Nh
- **关联需求**：REQ-NNN
- **状态**：🔲 待开始 / 🔄 进行中 / ✅ 已完成 / ❌ 已取消
- **创建时间**：YYYY-MM-DD
- **负责人**：<人名 / AI>

---

## 任务描述

> **具体要做什么**，以及为什么要做（背景）。  
> 这部分是给执行者（人或 AI）的上下文，写清楚目标，不写实现方案。

```
例：实现用户注册接口。
用户通过 POST /api/v1/auth/register 提交 email + password，
系统创建账号并发送验证邮件。
```

---

## 允许修改的文件范围

> ⚠️ **AI 只能修改以下列出的文件**，超出范围的修改需重新提交任务申请。  
> 这个范围在任务开始前由人工确认。

```
- `src/api/auth.py`           — 新增 /register 路由
- `src/services/user.py`      — 新增 create_user() 方法
- `src/schemas/user.py`       — 新增 RegisterRequest / RegisterResponse schema
- `tests/test_auth.py`        — 新增注册相关测试
```

---

## 不允许触碰的文件

> 以下文件当前已锁定（见 `LOCK.md`），**禁止任何修改**。  
> 如确实需要修改，请先通过解锁申请流程。

```
- `src/models/user.py`        — 已被 sprint-001 其他任务锁定
- `alembic/versions/*.py`     — Migration 文件永久锁定，只能新增
- `CONSTITUTION.md`           — 宪法文件，需人工审批才能修改
```

> （从 LOCK.md 同步，任务开始前检查一次）

---

## 实现要点

> **技术实现思路，给 AI 或开发者的上下文**。  
> 写关键决策和约束，不要写伪代码（那是 AI 的工作）。

```
1. 密码使用 bcrypt 哈希，不存明文（见 CONSTITUTION.md 安全红线）
2. 注册成功后调用 EmailService.send_verification()，异步发送不阻塞响应
3. 重复邮箱检测：在 DB 层用唯一约束 + Service 层 catch IntegrityError，返回 409
4. 请求体用 Pydantic V2，密码字段加 min_length=8 validator
5. 响应只返回 user_id 和 email，不返回密码 hash
```

---

## 验收标准

> **如何判断这个任务完成了**。每条标准必须可验证（有明确的测试方式）。

- [ ] `POST /api/v1/auth/register` 接口存在，Swagger 文档可见
- [ ] 正常注册返回 HTTP 201，body 包含 `user_id` 和 `email`
- [ ] 重复邮箱注册返回 HTTP 409，body 包含 `detail` 错误信息
- [ ] 密码不足 8 位返回 HTTP 422，body 包含具体的 validation error
- [ ] 注册成功后，数据库中密码字段不是明文（是 bcrypt hash）
- [ ] 注册成功后，发送验证邮件的方法被调用（mock 验证）

---

## 测试要求

- [ ] 单元测试：`tests/test_auth.py` 覆盖以上所有验收标准
- [ ] 运行 `python3 governance/arch-check.py` 无报错
- [ ] 运行 `git diff --cached --name-only | python3 governance/lock-check.py` 无报错
- [ ] `pytest tests/test_auth.py -v` 全部通过

---

## 完成记录

> **任务完成后填写**

- **完成时间**：YYYY-MM-DD HH:MM
- **实际工时**：Nh（预估 Nh）
- **实际修改文件**：
  - `src/api/auth.py` — 新增 register endpoint
  - `src/services/user.py` — 新增 create_user, check_email_exists
  - `src/schemas/user.py` — 新增 RegisterRequest, RegisterResponse
  - `tests/test_auth.py` — 新增 6 个测试用例
- **备注**：<任何需要记录的信息，例如技术决策、遇到的问题>
