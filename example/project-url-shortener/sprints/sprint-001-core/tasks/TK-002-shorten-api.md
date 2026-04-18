# TK-002: POST /api/shorten 接口，生成短码

## 基本信息

- **Sprint**：sprint-001-core
- **优先级**：P0
- **预估工时**：6h
- **关联需求**：REQ-001
- **状态**：✅ 已完成
- **创建时间**：2025-12-22
- **负责人**：AI

---

## 任务描述

实现短链接创建接口：用户通过 `POST /api/shorten` 提交一个长 URL，系统生成随机 8 位短码，将记录存入 `SHORT_LINK` 表，返回完整的短链接地址。

接口使用 FastAPI，请求体用 Pydantic V2 校验，响应返回 `short_code` 和完整的 `short_url`（如 `https://tinylink.io/aB3xK9mZ`）。

---

## 允许修改的文件范围

```
- `src/api/shorten.py`          — 新建 POST /api/shorten 路由
- `src/services/link.py`        — 新建 create_short_link() 服务方法
- `src/schemas/link.py`         — 新建 ShortenRequest / ShortenResponse schema
- `tests/test_shorten_api.py`   — 新增缩短接口测试
```

---

## 不允许触碰的文件

```
- `src/models/short_link.py`    — 已被 TK-001 使用并锁定（Sprint-001）
- `src/models/click_event.py`   — 同上
- `src/database.py`             — 数据库配置已稳定，不在本任务范围
- `CONSTITUTION.md`             — 宪法文件，需人工审批才能修改
```

---

## 实现要点

```
1. 请求体字段：original_url（必填，HTTP/HTTPS URL）、expires_at（可选，ISO 8601）
2. 短码生成：调用 nanoid(8)，生成后检查 DB 唯一性，碰撞时最多重试 3 次
3. 成功写入 SHORT_LINK 表后，返回 HTTP 201
4. 响应体包含：short_code, short_url（基础 URL + short_code），original_url, created_at
5. original_url 格式校验：Pydantic HttpUrl，禁止内网 IP（SSRF 防护，见 NFR-002）
6. 使用 AsyncSession，确保接口异步非阻塞
```

---

## 验收标准

- [x] `POST /api/shorten` 接口存在，FastAPI Swagger 文档可见
- [x] 提交合法 URL，返回 HTTP 201，body 包含 `short_code`（8 位）和 `short_url`
- [x] 提交非法 URL 格式，返回 HTTP 422，body 包含 validation error 详情
- [x] 生成的短码在 DB 中唯一（测试：连续创建 100 条，无重复）
- [x] 传入 `expires_at` 时，`SHORT_LINK` 记录中 `expires_at` 字段正确存储
- [x] 提交内网 IP URL（如 `http://192.168.1.1/`），返回 HTTP 422

---

## 测试要求

- [x] 单元测试：`tests/test_shorten_api.py` 覆盖以上所有验收标准
- [x] 运行 `python3 governance/arch-check.py` 无报错
- [x] 运行 `git diff --cached --name-only | python3 governance/lock-check.py` 无报错
- [x] `pytest tests/test_shorten_api.py -v` 全部通过

---

## 完成记录

- **完成时间**：2025-12-25 20:30
- **实际工时**：6h（预估 6h）
- **实际修改文件**：
  - `src/api/shorten.py` — POST /api/shorten endpoint
  - `src/services/link.py` — create_short_link(), check_code_unique()
  - `src/schemas/link.py` — ShortenRequest, ShortenResponse
  - `tests/test_shorten_api.py` — 7 个测试用例，全部通过
- **备注**：SSRF 防护使用 `ipaddress` 标准库校验，拒绝私有 IP 段（10.x, 172.16.x, 192.168.x）
