# CH-NNN Impact Assessment

> **说明**：本文件由 `python3 governance/impact.py <project-id> CH-NNN` 自动生成。  
> 人工审查后，通过 `apply-and-archive.py apply` 确认实施。

---

## LOCK 扫描结果

> 由 `impact.py` 自动填写，对照 `LOCK.md` 扫描 delta.md 中涉及的文件。

| 文件 | 锁定状态 | 锁定 Sprint | 影响程度 |
|-----|---------|-----------|---------|
| `src/models/user.py` | 🔒 锁定中 | sprint-001 | 高（需修改核心 Model） |
| `src/api/auth.py` | 🔒 锁定中 | sprint-001 | 中（新增路由） |
| `src/services/user.py` | ✅ 未锁定 | - | 中（新增 Service 方法） |
| `src/schemas/user.py` | ✅ 未锁定 | - | 低（新增 Schema） |

---

## 模块影响分析

> 列出受影响的模块和原因

| 模块 | 影响类型 | 说明 |
|------|---------|------|
| `src/models/user.py` | **Schema 变更** | 新增 `phone` 字段，需要 migration |
| `src/api/auth.py` | **接口新增** | 新增 `/sms/send` 接口 |
| `src/services/user.py` | **方法新增** | 新增 `create_user_by_phone()` |
| `alembic/versions/` | **Migration 新增** | 需要新增 phone 字段的 migration |

---

## 下游依赖

> 依赖受影响模块的其他模块

| 受影响模块 | 依赖它的模块 | 风险说明 |
|---------|-----------|---------|
| `src/models/user.py` | `src/services/user.py`, `src/api/auth.py`, `src/api/profile.py` | Schema 变更需验证所有依赖方兼容性 |
| `src/services/user.py` | `src/api/auth.py` | 接口层直接调用，需同步更新 |

---

## 风险等级

- [ ] **低**（不触及任何锁定文件，影响范围明确）
- [x] **中**（触及锁定文件，但影响范围明确，有缓解措施）
- [ ] **高**（触及多个锁定文件或核心架构，需要特别评审）

**风险说明**：
```
触及 2 个锁定文件（sprint-001 进行中），需要提交解锁申请。
数据库 Schema 变更风险可控（新增 nullable 字段，向后兼容）。
建议在 sprint-001 归档后再实施，或申请解锁并确认不影响进行中任务。
```

---

## 解锁申请建议

> 根据 LOCK 扫描结果，建议提交以下解锁申请

| 文件 | 建议操作 |
|------|---------|
| `src/models/user.py` | 在 LOCK.md 解锁申请表中登记，等待 sprint-001 任务负责人确认 |
| `src/api/auth.py` | 同上 |

---

## 审批建议

> `impact.py` 自动生成的审批建议，基于风险等级和锁定情况

```
⚠️  中风险变更

建议：
1. 申请解锁 src/models/user.py 和 src/api/auth.py
2. 与 sprint-001 负责人对齐，确认不冲突
3. 在解锁申请审批通过后，再执行 apply 操作
4. 实施前：先创建 migration，测试数据库升级/回滚

预计实施时间：N 小时
```

---

## 生成信息

- **生成时间**：YYYY-MM-DD HH:MM
- **生成工具**：`governance/impact.py`
- **输入文件**：`changes/active/CH-NNN/delta.md`
