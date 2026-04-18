# TK-001: 创建 SHORT_LINK 和 CLICK_EVENT 数据模型

## 基本信息

- **Sprint**：sprint-001-core
- **优先级**：P0
- **预估工时**：4h
- **关联需求**：REQ-001, REQ-005
- **状态**：✅ 已完成
- **创建时间**：2025-12-20
- **负责人**：AI

---

## 任务描述

创建 TinyLink 系统的两个核心数据模型：

1. **SHORT_LINK**：存储短链接记录，包括 nanoid 8 位 ID、原始 URL、创建时间、过期时间、点击计数
2. **CLICK_EVENT**：存储每次点击事件，包括关联的短链接 ID、IP 哈希、User-Agent、点击时间

模型使用 SQLAlchemy（asyncpg），短码 ID 用 nanoid 生成（8 位 `[a-zA-Z0-9]`），非自增整型，以保证 URL 安全。

---

## 允许修改的文件范围

```
- `src/models/short_link.py`    — 新建 ShortLink ORM 模型
- `src/models/click_event.py`   — 新建 ClickEvent ORM 模型
- `src/database.py`             — 数据库连接和 Base 声明
- `alembic/versions/001_init.py` — 初始 migration
- `tests/test_models.py`        — 数据模型单元测试
```

---

## 不允许触碰的文件

```
- `CONSTITUTION.md`             — 宪法文件，需人工审批才能修改
- `governance/`                 — 治理脚本，不在本任务范围内
```

> （本任务为 Sprint-001 第一个任务，LOCK.md 尚未有锁定文件）

---

## 实现要点

```
1. SHORT_LINK.id 使用 nanoid(8)，存为 VARCHAR(8)，设为主键
2. SHORT_LINK.custom_alias 暂不添加（CH-001 变更时再加），当前 schema 只含核心字段
3. CLICK_EVENT.ip_hash 使用 SHA-256 哈希存储，禁止明文 IP（见 CONSTITUTION.md 安全红线）
4. CLICK_EVENT.user_agent 截断至 512 字符，防止过大数据写入
5. SHORT_LINK.click_count 用于快速展示，异步更新（不用每次 JOIN CLICK_EVENT 聚合）
6. 两个模型使用 SQLAlchemy AsyncSession，配合 asyncpg 驱动
7. 时间字段统一用 datetime(timezone=True)，存 UTC
```

---

## 验收标准

- [x] `src/models/short_link.py` 存在，包含 ShortLink 类，字段齐全（id, original_url, created_at, expires_at, click_count）
- [x] `src/models/click_event.py` 存在，包含 ClickEvent 类，字段齐全（id, link_id, ip_hash, user_agent, clicked_at）
- [x] `SHORT_LINK` 与 `CLICK_EVENT` 之间有正确的外键关联（link_id → short_link.id）
- [x] Migration 文件存在，`alembic upgrade head` 可成功建表
- [x] `tests/test_models.py` 测试：创建 ShortLink 记录、创建 ClickEvent 并关联、查询通过

---

## 测试要求

- [x] 单元测试：`tests/test_models.py` 覆盖以上所有验收标准
- [x] 运行 `python3 governance/arch-check.py` 无报错
- [x] 运行 `git diff --cached --name-only | python3 governance/lock-check.py` 无报错
- [x] `pytest tests/test_models.py -v` 全部通过

---

## 完成记录

- **完成时间**：2025-12-22 18:00
- **实际工时**：4h（预估 4h）
- **实际修改文件**：
  - `src/models/short_link.py` — 新建 ShortLink 模型（6 个字段）
  - `src/models/click_event.py` — 新建 ClickEvent 模型（5 个字段）
  - `src/database.py` — AsyncSession + Base 声明
  - `alembic/versions/001_init.py` — 初始建表 migration
  - `tests/test_models.py` — 5 个测试用例，全部通过
- **备注**：nanoid 生成使用 `python-nanoid` 库，已加入 requirements.txt
