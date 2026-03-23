# To-Do List API

Dự án API to-do list sử dụng FastAPI. Xây dựng theo từng cấp độ từ cơ bản đến nâng cao.

## Cấu trúc giai đoạn

- **Cấp 0**: Hello To-Do (API minimal)
- **Cấp 1**: CRUD cơ bản (dữ liệu RAM)
- **Cấp 2**: Validation + filter/sort/pagination
- **Cấp 3**: Tách tầng (router/service/repository)
- **Cấp 4**: Database + ORM (SQLAlchemy)
- **Cấp 5**: Authentication + User management
- **Cấp 6**: Tags + Deadline + Overdue tracking
- **Cấp 7**: Testing + Dockerfile
- **Cấp 8**: Soft delete

## Cháy độ - Hướng dẫn cài đặt

### Cấp 0: Hello To-Do

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
uvicorn main:app --reload

# Kiểm tra:
# GET http://localhost:8000/health → {"status": "ok"}
# GET http://localhost:8000/ → {"message": "Welcome to To-Do API"}
```

**Tiến tới Cấp 1:** Khi sẵn sàng, hãy chạy:
```bash
git add .
git commit -m "Cấp 0: Hello To-Do - API minimal"
```

Sau đó chuyển sang hướng dẫn Cấp 1.
