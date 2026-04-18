# TK-003: GET /{code} 重定向接口 + 点击记录

## 基本信息

- **Sprint**：sprint-001-core
- **优先级**：P0
- **预估工时**：5h
- **关联需求**：REQ-004, REQ-005
- **状态**：✅ 已完成
- **创建时间**：2025-12-25
- **负责人**：AI

---

## 任务描述

实现短链接重定向接口：用户访问 `GET /{code}`，系统查询短码对应的原始 URL，返回 HTTP 302 重定向。同时异步将本次点击写入 `CLICK_EVENT` 表（不阻塞重定向响应）。

过期短链接返回 HTTP 410，不存在的短码返回 HTTP 404。

---

## 允许修改的文件范围

```
- `src/api/redirect.py`         — 新建 GET /{code} 路由
- `src/services/link.py`        — 新增 get_link_by_code(), record_click() 方法
- `src/utils/ip.py`             — 新建 IP 哈希工具函数
- `tests/test_redirect_api.py`  — 新增重定向接口测试
```

---

## 不允许触碰的文件

```
- `src/models/short_link.py`    — 已锁定（Sprint-001），不允许修改
- `src/models/click_event.py`   — 已锁定（Sprint-001），不允许修改
- `src/api/shorten.py`          — TK-002 已完成并锁定，不允许修改
- `src/database.py`             — 数据库配置已稳定
- `CONSTITUTION.md`             — 宪法文件，需人工审批才能修改
```

---

## 实现要点

```
1. 路由注册为最低优先级（在所有 /api/* 路由之后），避免遮蔽其他接口
2. 查询短码：先查 DB，获取 original_url 和 expires_at
3. 过期检查：expires_at 不为空且 < now()，返回 HTTP 410
4. 重定向：返回 RedirectResponse(url=original_url, status_code=302)
5. 点击记录（异步，不阻塞）：
   - 取 X-Forwarded-For / REMOTE_ADDR，SHA-256 哈希存入 ip_hash
   - User-Agent 截断至 512 字符
   - 使用 asyncio.create_task() 后台写入 CLICK_EVENT
   - 同时异步 UPDATE short_link SET click_count = click_count + 1
6. 不存在的短码：返回 HTTP 404，JSON body `{"detail": "link not found"}`
```

---

## 验收标准

- [x] `GET /{code}` 路由存在，有效短码返回 HTTP 302，`Location` 头指向原始 URL
- [x] 重定向后，`CLICK_EVENT` 表中有对应记录（link_id、ip_hash、user_agent、clicked_at）
- [x] `CLICK_EVENT.ip_hash` 是 SHA-256 哈希，非明文 IP（验证：字段长度 64 位十六进制）
- [x] 访问不存在短码，返回 HTTP 404
- [x] 访问已过期短链接，返回 HTTP 410
- [x] 点击记录写入不阻塞重定向响应（测试：mock asyncio.create_task 验证异步调用）
- [x] `SHORT_LINK.click_count` 在点击后递增 1

---

## 测试要求

- [x] 单元测试：`tests/test_redirect_api.py` 覆盖以上所有验收标准
- [x] 运行 `python3 governance/arch-check.py` 无报错
- [x] 运行 `git diff --cached --name-only | python3 governance/lock-check.py` 无报错
- [x] `pytest tests/test_redirect_api.py -v` 全部通过

---

## 完成记录

- **完成时间**：2026-01-03 16:00
- **实际工时**：5h（预估 5h）
- **实际修改文件**：
  - `src/api/redirect.py` — GET /{code} endpoint，302/404/410 逻辑
  - `src/services/link.py` — get_link_by_code(), record_click()（追加到 TK-002 建立的文件）
  - `src/utils/ip.py` — hash_ip() 工具函数（SHA-256）
  - `tests/test_redirect_api.py` — 8 个测试用例，全部通过
- **备注**：`click_count` 递增用 `UPDATE ... SET click_count = click_count + 1 WHERE id = :id`，避免 read-modify-write 竞争。高并发下 Sprint-002 再改 Redis INCR。
