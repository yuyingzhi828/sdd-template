# CH-001 Delta

> **说明**：本文件描述对 RFC.md 的精确变更。  
> 归档后，需手动将这里的变更合并回 RFC.md。
>
> **机器可读标记格式**：
> ```
> <!-- [ACTION] REQ-ID: 说明 -->
> ACTION 可选值：ADD | MODIFY | DELETE
> ```

---

## 对 RFC.md 的变更

### 修改需求

<!-- [MODIFY] REQ-001: 原文"生成随机8位短码" → 新文"生成随机8位短码，支持用户指定自定义别名" -->

| 字段 | 原文 | 新文 |
|------|------|------|
| 描述 | 用户通过 POST /api/shorten 提交长 URL，系统生成随机 8 位短码 | 用户通过 POST /api/shorten 提交长 URL，系统生成随机 8 位短码，**支持用户指定自定义别名** |
| 验收标准（新增） | — | 用户可选传入 `custom_alias` 字段（1-32 位，`[a-zA-Z0-9_-]`） |
| 关联 | 无 | REQ-007 |

---

### 新增需求

<!-- [ADD] REQ-007: 自定义别名唯一性校验，冲突返回 409 -->

```markdown
### REQ-007: 自定义别名唯一性校验

- **描述**：创建短链接时若指定 `custom_alias`，系统校验别名唯一性，冲突返回 409
- **验收标准**：
  - 别名已存在时返回 HTTP 409，body 包含 `detail: "alias already taken"`
  - 别名格式不合法（含特殊字符、超长）返回 HTTP 422
  - 别名与随机短码共用同一命名空间，不允许冲突
- **优先级**：P1
- **状态**：implemented
- **关联**：REQ-001
```

---

## 涉及的锁定文件

| 文件 | 是否锁定 | 锁定所属 Sprint | 需要解锁申请 |
|-----|---------|--------------|-----------|
| `src/models/short_link.py` | ✅ 是 | sprint-001 | 是（CH-001 已申请，已批准） |
| `src/api/shorten.py` | ❌ 否 | - | 否 |
| `src/services/link.py` | ❌ 否 | - | 否 |

---

## 数据库变更

```sql
-- 新增 custom_alias 字段
ALTER TABLE short_link ADD COLUMN custom_alias VARCHAR(32) UNIQUE;

-- 说明：nullable，兼容现有无别名的短链接记录
-- UNIQUE 约束确保别名全局唯一
```

---

## API 变更

| 操作 | 方法 | 路径 | 变更类型 |
|------|------|------|---------|
| 修改 | POST | `/api/shorten` | request body 新增 `custom_alias` 可选字段 |
| 新增错误码 | POST | `/api/shorten` | 别名冲突时返回 HTTP 409 |
