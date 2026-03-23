# To-Do List API - Progressive Development Guide

API quản lý công việc xây dựng theo **6 cấp độ** từ cơ bản đến nâng cao.

> **Status**: ✅ Hoàn tất Cấp 1-6 | **45 tests** (30 + 15) | **0 warnings**

---

## 📊 6 Cấp Độ

| Cấp | Tên | Tính Năng | Status |
|-----|-----|----------|--------|
| **1** | CRUD Cơ Bản | 5 endpoints (POST/GET/PUT/DELETE) | ✓ |
| **2** | Validation + Query | Validate, filter, search, sort, pagination | ✓ |
| **3** | Layered Architecture | Router/Service/Repository, config, clean code | ✓ |
| **4** | Database + ORM | SQLAlchemy, SQLite, timestamps, PATCH | ✓ |
| **5** | Authentication | JWT, multi-user, todo ownership | ✓ |
| **6** | Advanced Features | due_date, tags, overdue/today endpoints | ✓ |

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
# Chạy tất cả tests: 45 tests (30 Cấp 1-5 + 15 Cấp 6)
pytest test_todos.py -v

# Chạy theo cấp độ
pytest test_todos.py::TestAuthentication -v         # Cấp 5: Auth (10 tests)
pytest test_todos.py::TestValidation -v             # Cấp 2: Validation (4 tests)
pytest test_todos.py::TestDatabase -v               # Cấp 4: Database (6 tests)
pytest test_todos.py::TestLevel6Advanced -v         # Cấp 6: Advanced (15 tests)

# Chi tiết
pytest test_todos.py::TestLevel6Advanced::test_create_todo_with_due_date -v
```

**Result**: ✓ 45/45 PASSED | Cấp 1-6 hoàn tất | ~3.5 seconds

---

### **Manual Test (cURL)**

**Cấp 6 - Advanced Features (due_date, tags)**
```bash
# Tạo todo với deadline
curl -X POST http://localhost:8000/api/v1/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project",
    "due_date": "2026-03-25T23:59:59",
    "tags": ["urgent", "work"]
  }'

# Lấy todo quá hạn
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/todos/overdue

# Lấy todo hôm nay
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/todos/today

# Cập nhật tags
curl -X PATCH http://localhost:8000/api/v1/todos/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["high-priority", "backend"]}'
```

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

**Cấp 5 - Authentication & Multi-User**
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@example.com", "password": "securepass123"}'

# Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@example.com", "password": "securepass123"}' \
  | jq -r '.access_token')

# Get current user info
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/me

# Create todo with authentication
curl -X POST http://localhost:8000/api/v1/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Task"}'

# Get user's todos (isolated view)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/todos

# User A cannot access User B's todos (returns 404)
curl -H "Authorization: Bearer $TOKEN_B" \
  http://localhost:8000/api/v1/todos/1  # Created by User A
```

---

## 📋 Validation Rules

| Field | Rule | Example |
|-------|------|---------|
| `title` | Bắt buộc, 3-100 chars | "Learn FastAPI" ✓ |
| `description` | Tùy chọn, max 500 chars | "Framework..." |
| `is_done` | Boolean (default: false) | true / false |
| `due_date` | Tùy chọn, ISO datetime | "2026-03-25T23:59:59" |
| `tags` | Danh sách tag (default: []) | ["work", "urgent"] |
| `limit` | 1-100 (default: 10) | 5 ✓, 200 ✗ |
| `offset` | ≥ 0 (default: 0) | 0 ✓, -1 ✗ |

---

## 📝 API Endpoints

| Method | Endpoint | Cấp |
|--------|----------|-----|
| POST | `/api/v1/auth/register` | 5 |
| POST | `/api/v1/auth/login` | 5 |
| GET | `/api/v1/auth/me` | 5 |
| POST | `/api/v1/todos` | 1-5 * |
| GET | `/api/v1/todos` | 2-5 * |
| GET | `/api/v1/todos/overdue` | 6 * |
| GET | `/api/v1/todos/today` | 6 * |
| GET | `/api/v1/todos/{id}` | 1-5 * |
| PUT | `/api/v1/todos/{id}` | 1-5 * |
| PATCH | `/api/v1/todos/{id}` | 4-5 * |
| DELETE | `/api/v1/todos/{id}` | 1-5 * |
| GET | `/health` | 3-6 |
| GET | `/` | 3-6 |

`*` From Cấp 5+, requires `Authorization: Bearer {token}`

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
- **Tests**: **6 tests**

### Cấp 5 (Authentication + Multi-User)
- [x] User registration (email validation, password hashing)
- [x] User login (credentials validation)
- [x] JWT token generation & validation
- [x] Bearer token authorization on todo endpoints
- [x] User isolation (todos filtered by owner_id)
- [x] Cross-user access prevention
- [x] Password hashing with bcrypt/pbkdf2
- **Tests**: **10 (auth) + 5 (user ownership) = 15 tests**

### Cấp 6 (Advanced Features)
- [x] Due date (deadline) field
- [x] Tags field (multiple tags per todo)
- [x] GET /todos/overdue endpoint (list overdue tasks)
- [x] GET /todos/today endpoint (list today's tasks)
- [x] Filter by due_date
- [x] User-scoped overdue/today filtering
- [x] Update todo with due_date & tags
- **Tests**: **15 tests** (create with dates/tags, update, overdue, today, sorting, multiple tags)

### **Total: 45 tests ✅** (30 Cấp 1-5 + 15 Cấp 6)

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

- [test_todos.py](test_todos.py) - 45 unit tests (30 Cấp 1-5 + 15 Cấp 6 - consolidated)
- [main.py](main.py) - Entry point  
- [requirements.txt](requirements.txt) - Dependencies
