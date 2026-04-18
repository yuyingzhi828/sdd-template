# CH-001 实施任务清单

> **说明**：本文件记录 CH-001 变更的具体实施任务，在 Sprint 003 中执行。

---

## 任务清单

| 任务 | 负责人 | 状态 |
|------|--------|------|
| 在 LOCK.md 提交解锁申请（models/short_link.py） | TinyLink 团队 | ✅ 已完成 |
| 等待解锁申请审批 | TinyLink 团队 | ✅ 已完成（2026-01-16 批准） |
| 执行数据库迁移：`ALTER TABLE short_link ADD COLUMN custom_alias VARCHAR(32) UNIQUE` | TinyLink 团队 | ✅ 已完成 |
| 更新 `src/models/short_link.py`：新增 `custom_alias` 字段 | TinyLink 团队 | ✅ 已完成 |
| 更新 `src/api/shorten.py`：接收 `custom_alias` 参数 | TinyLink 团队 | ✅ 已完成 |
| 更新 `src/services/link.py`：新增别名唯一性校验逻辑 | TinyLink 团队 | ✅ 已完成 |
| 新增测试：别名冲突返回 409，格式非法返回 422 | TinyLink 团队 | ✅ 已完成 |
| 更新 RFC.md（合并 delta.md 变更，REQ-001 修改、REQ-007 新增） | TinyLink 团队 | ✅ 已完成 |
| 运行 `lock-check.py`，确认无违规 | TinyLink 团队 | ✅ 已完成 |
| 执行 `apply-and-archive.py archive`，移入归档目录 | TinyLink 团队 | ✅ 已完成 |

---

## 验收确认

- [x] `custom_alias` 字段存入数据库，可通过 GET /api/links/{code} 查询到
- [x] 自定义别名冲突返回 HTTP 409
- [x] 别名格式非法返回 HTTP 422
- [x] 已有随机短码的短链接不受影响
- [x] 所有测试通过，覆盖率 ≥ 80%
- [x] RFC.md 已同步更新（REQ-001 + REQ-007）
- [x] RFC_CHANGELOG.md 已追加归档记录
