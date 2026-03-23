# To-Do List API - Progressive Development Guide

API quản lý công việc xây dựng theo **5 cấp độ** từ cơ bản đến nâng cao.

> **Status**: ✅ Hoàn tất Cấp 1-4 | **34 tests** | **0 warnings** | 📋 Cấp 5 (Roadmap)

---

## 📊 5 Cấp Độ

| Cấp | Tên | Tính Năng | Status |
|-----|-----|----------|--------|
| **1** | CRUD Cơ Bản | 5 endpoints (POST/GET/PUT/DELETE) | ✓ |
| **2** | Validation + Query | Validate, filter, search, sort, pagination | ✓ |
| **3** | Layered Architecture | Router/Service/Repository, config, clean code | ✓ |
| **4** | Database + ORM | SQLAlchemy, SQLite, timestamps, PATCH | ✓ |
| **5** | Authentication | JWT, multi-user, todo ownership | 📋 |

---

## 🚀 Setup

```bash
# Cài đặt
pip install -r requirements.txt

# Chạy server
uvicorn main:app --reload

# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## 🧪 Test

### **Unit Tests (Khuyến nghị)** ⭐

```bash
# Chạy tất cả 34 tests
pytest test_todos.py -v

# Chạy theo cấp độ
pytest test_todos.py::TestValidation -v          # Cấp 2: Validation (9 tests)
pytest test_todos.py::TestFilterSearchSort -v    # Cấp 2: Filter/Sort/Pagination (12 tests)
pytest test_todos.py::TestLayeredArchitecture -v # Cấp 3: Architecture (5 tests)
pytest test_todos.py::TestDatabase -v            # Cấp 4: Database (10+ tests)

# Chi tiết
pytest test_todos.py -vv
pytest test_todos.py::TestValidation::test_title_too_short -v
```

**Result**: ✓ 34/34 PASSED | ~2 seconds

---

### **Manual Test (cURL)**

**Cấp 2 - Validation**
```bash
# ✓ Valid (title 3-100 chars)
curl -X POST http://localhost:8000/api/v1/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI"}'

# ✗ Invalid (title < 3)
curl -X POST http://localhost:8000/api/v1/todos \
  -d '{"title": "ab"}' → 422
```

**Cấp 2 - Filter/Search/Sort/Pagination**
```bash
# Filter
curl "http://localhost:8000/api/v1/todos?is_done=false"

# Search (case-insensitive)
curl "http://localhost:8000/api/v1/todos?q=fastapi"

# Sort
curl "http://localhost:8000/api/v1/todos?sort=-created_at"

# Pagination
curl "http://localhost:8000/api/v1/todos?limit=5&offset=0"

# Combined
curl "http://localhost:8000/api/v1/todos?is_done=false&q=api&sort=-created_at&limit=5"
```

**Cấp 3 - Architecture**
```bash
curl http://localhost:8000/health     # Health check
curl http://localhost:8000/           # Root
curl http://localhost:8000/api/v1/todos # API v1 prefix
```

**Cấp 4 - Database & PATCH**
```bash
# Create
curl -X POST http://localhost:8000/api/v1/todos \
  -d '{"title": "Task", "description": "Desc", "is_done": false}'

# PATCH (partial update)
curl -X PATCH http://localhost:8000/api/v1/todos/1 \
  -d '{"is_done": true}'
  # → title, description unchanged, is_done=true, updated_at updated

# Timestamps
curl http://localhost:8000/api/v1/todos/1 | jq '.created_at, .updated_at'
```

---

## 📋 Validation Rules

| Field | Rule | Example |
|-------|------|---------|
| `title` | Bắt buộc, 3-100 chars | "Learn FastAPI" ✓ |
| `description` | Tùy chọn, max 500 chars | "Framework..." |
| `is_done` | Boolean (default: false) | true / false |
| `limit` | 1-100 (default: 10) | 5 ✓, 200 ✗ |
| `offset` | ≥ 0 (default: 0) | 0 ✓, -1 ✗ |

---

## 📝 API Endpoints

| Method | Endpoint | Cấp |
|--------|----------|-----|
| POST | `/api/v1/todos` | 1-4 |
| GET | `/api/v1/todos` | 2-4 |
| GET | `/api/v1/todos/{id}` | 1-4 |
| PUT | `/api/v1/todos/{id}` | 1-4 |
| PATCH | `/api/v1/todos/{id}` | 4 |
| DELETE | `/api/v1/todos/{id}` | 1-4 |
| GET | `/health` | 3-4 |
| GET | `/` | 3-4 |

---

## ✅ Test Coverage

### Cấp 2 (Validation + Query)
- [x] Title validation (3-100 chars)
- [x] Filter by `is_done`
- [x] Search by `q` (case-insensitive)
- [x] Sort by `created_at` (asc/desc)
- [x] Pagination (limit, offset)
- [x] Response: `{ items, total, limit, offset }`
- **Tests**: 9 (validation) + 12 (filter/sort) = **21 tests**

### Cấp 3 (Layered Architecture)
- [x] Routers (no DB logic)
- [x] Services (business logic)
- [x] Repositories (queries)
- [x] Schemas (Pydantic)
- [x] Config (pydantic-settings)
- [x] API prefix `/api/v1`
- **Tests**: **5 tests**

### Cấp 4 (Database + ORM)
- [x] SQLAlchemy + SQLite
- [x] Auto timestamps (created_at, updated_at)
- [x] PATCH partial update
- [x] Pagination from DB
- [x] 404 error handling
- **Tests**: **10+ tests**

### **Total: 34 tests ✅**

---

## 🏗 Cấu Trúc

```
app/
├── core/          → Config, DB setup, ORM models
├── routers/       → API endpoints
├── services/      → Business logic
├── repositories/  → DB queries
└── schemas/       → Pydantic validation
```

---

## 🔗 Files

- [test_todos.py](test_todos.py) - 34 unit tests
- [main.py](main.py) - Entry point
- [requirements.txt](requirements.txt) - Dependencies
