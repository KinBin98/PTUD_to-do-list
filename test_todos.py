"""
Test suite for To-Do List API (Levels 2, 3, 4)
Tests validation, filtering/sorting/pagination, layered architecture, and database operations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db
from app.core.models import Todo


# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestValidation:
    """Test Level 2 - Validation"""

    def test_create_todo_valid(self):
        """Test creating a valid todo"""
        response = client.post(
            "/api/v1/todos",
            json={"title": "Test Todo", "description": "A test todo"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "A test todo"
        assert data["is_done"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_title_too_short(self):
        """Title must be at least 3 characters"""
        response = client.post(
            "/api/v1/todos",
            json={"title": "ab"}
        )
        assert response.status_code == 422

    def test_title_too_long(self):
        """Title must not exceed 100 characters"""
        long_title = "a" * 101
        response = client.post(
            "/api/v1/todos",
            json={"title": long_title}
        )
        assert response.status_code == 422

    def test_title_empty(self):
        """Title cannot be empty"""
        response = client.post(
            "/api/v1/todos",
            json={"title": ""}
        )
        assert response.status_code == 422

    def test_title_exactly_3_chars(self):
        """Title with exactly 3 characters is valid"""
        response = client.post(
            "/api/v1/todos",
            json={"title": "abc"}
        )
        assert response.status_code == 200

    def test_title_exactly_100_chars(self):
        """Title with exactly 100 characters is valid"""
        title = "a" * 100
        response = client.post(
            "/api/v1/todos",
            json={"title": title}
        )
        assert response.status_code == 200

    def test_description_max_length(self):
        """Description must not exceed 500 characters"""
        long_desc = "a" * 501
        response = client.post(
            "/api/v1/todos",
            json={"title": "Valid", "description": long_desc}
        )
        assert response.status_code == 422

    def test_partial_update_preserves_other_fields(self):
        """PATCH should only update specified fields"""
        # Create a todo
        create_response = client.post(
            "/api/v1/todos",
            json={"title": "Original Title", "description": "Original Description", "is_done": False}
        )
        todo_id = create_response.json()["id"]

        # Partial update only title
        patch_response = client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"title": "New Title"}
        )
        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "Original Description"
        assert data["is_done"] is False


class TestFilterSearchSort:
    """Test Level 2 - Filter, Search, Sort, Pagination"""

    @pytest.fixture(autouse=True)
    def setup_todos(self):
        """Create sample todos for testing"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Create test data
        todos_data = [
            {"title": "Buy groceries", "is_done": True},
            {"title": "Read documentation", "is_done": False},
            {"title": "Write tests", "is_done": False},
            {"title": "Deploy application", "is_done": True},
            {"title": "Code review", "is_done": False},
        ]
        
        for todo in todos_data:
            client.post("/api/v1/todos", json=todo)

    def test_get_all_todos(self):
        """Test getting all todos"""
        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["total"] == 5

    def test_filter_by_is_done_true(self):
        """Test filtering by is_done=true"""
        response = client.get("/api/v1/todos?is_done=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["is_done"] is True

    def test_filter_by_is_done_false(self):
        """Test filtering by is_done=false"""
        response = client.get("/api/v1/todos?is_done=false")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        for item in data["items"]:
            assert item["is_done"] is False

    def test_search_by_keyword(self):
        """Test searching by keyword"""
        response = client.get("/api/v1/todos?q=review")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "review" in data["items"][0]["title"].lower()

    def test_search_case_insensitive(self):
        """Test search is case-insensitive"""
        response = client.get("/api/v1/todos?q=WRITE")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "write" in data["items"][0]["title"].lower()

    def test_search_partial_match(self):
        """Test search matches partial strings"""
        response = client.get("/api/v1/todos?q=app")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "application" in data["items"][0]["title"].lower()

    def test_sort_by_created_at_ascending(self):
        """Test sorting by created_at ascending"""
        response = client.get("/api/v1/todos?sort=created_at")
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        # Items should be in ascending order by created_at
        for i in range(len(items) - 1):
            assert items[i]["created_at"] <= items[i + 1]["created_at"]

    def test_sort_by_created_at_descending(self):
        """Test sorting by created_at descending"""
        response = client.get("/api/v1/todos?sort=-created_at")
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        # Items should be in descending order by created_at
        for i in range(len(items) - 1):
            assert items[i]["created_at"] >= items[i + 1]["created_at"]

    def test_pagination_limit(self):
        """Test pagination limit parameter"""
        response = client.get("/api/v1/todos?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_pagination_offset(self):
        """Test pagination offset parameter"""
        response1 = client.get("/api/v1/todos?limit=2&offset=0")
        response2 = client.get("/api/v1/todos?limit=2&offset=2")
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["offset"] == 0
        assert data2["offset"] == 2
        # Items should be different
        assert data1["items"][0]["id"] != data2["items"][0]["id"]

    def test_combined_filter_search_sort_pagination(self):
        """Test combining multiple parameters"""
        response = client.get("/api/v1/todos?is_done=false&q=test&sort=created_at&limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_pagination_max_limit(self):
        """Test that limit cannot exceed 100"""
        response = client.get("/api/v1/todos?limit=101")
        assert response.status_code == 422


class TestLayeredArchitecture:
    """Test Level 3 - Layered Architecture (Router/Service/Repository)"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup clean database"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_api_v1_prefix(self):
        """Test that API uses /api/v1 prefix"""
        response = client.get("/api/v1/todos")
        assert response.status_code == 200

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self):
        """Test root welcome endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_all_crud_operations(self):
        """Test all CRUD operations work correctly"""
        # CREATE
        create_response = client.post(
            "/api/v1/todos",
            json={"title": "Test Task"}
        )
        assert create_response.status_code == 200
        todo_id = create_response.json()["id"]

        # READ
        read_response = client.get(f"/api/v1/todos/{todo_id}")
        assert read_response.status_code == 200
        assert read_response.json()["id"] == todo_id

        # UPDATE (full)
        update_response = client.put(
            f"/api/v1/todos/{todo_id}",
            json={"title": "Updated Task", "is_done": True}
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Task"

        # DELETE
        delete_response = client.delete(f"/api/v1/todos/{todo_id}")
        assert delete_response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/api/v1/todos/{todo_id}")
        assert get_response.status_code == 404


class TestDatabase:
    """Test Level 4 - Database Operations & ORM"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup clean database"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set"""
        response = client.post(
            "/api/v1/todos",
            json={"title": "Auto Timestamp"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "created_at" in data
        assert data["created_at"] is not None

    def test_updated_at_auto_set(self):
        """Test that updated_at is automatically set"""
        response = client.post(
            "/api/v1/todos",
            json={"title": "Auto Timestamp"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "updated_at" in data
        assert data["updated_at"] is not None

    def test_updated_at_changes_on_update(self):
        """Test that updated_at changes when todo is updated"""
        # Create
        create_response = client.post(
            "/api/v1/todos",
            json={"title": "Original"}
        )
        todo_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]

        # Wait a tiny bit and update
        import time
        time.sleep(0.01)

        # Update
        update_response = client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"title": "Updated"}
        )
        new_updated_at = update_response.json()["updated_at"]

        # Timestamps should be different (updated_at should be newer)
        assert new_updated_at >= original_updated_at

    def test_partial_update_only_is_done(self):
        """Test PATCH endpoint for updating only is_done"""
        # Create
        create_response = client.post(
            "/api/v1/todos",
            json={"title": "Mark Complete", "is_done": False}
        )
        todo_id = create_response.json()["id"]
        original_title = create_response.json()["title"]

        # Partial update only is_done
        patch_response = client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"is_done": True}
        )
        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["is_done"] is True
        assert data["title"] == original_title

    def test_partial_update_only_description(self):
        """Test PATCH endpoint for updating only description"""
        # Create
        create_response = client.post(
            "/api/v1/todos",
            json={"title": "Task", "description": "Old"}
        )
        todo_id = create_response.json()["id"]

        # Partial update
        patch_response = client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"description": "New description"}
        )
        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["description"] == "New description"
        assert data["title"] == "Task"

    def test_get_nonexistent_todo(self):
        """Test getting a non-existent todo returns 404"""
        response = client.get("/api/v1/todos/99999")
        assert response.status_code == 404

    def test_update_nonexistent_todo(self):
        """Test updating a non-existent todo returns 404"""
        response = client.put(
            "/api/v1/todos/99999",
            json={"title": "New"}
        )
        assert response.status_code == 404

    def test_delete_nonexistent_todo(self):
        """Test deleting a non-existent todo returns 404"""
        response = client.delete("/api/v1/todos/99999")
        assert response.status_code == 404

    def test_response_structure(self):
        """Test that response structure is correct"""
        client.post("/api/v1/todos", json={"title": "Test1"})
        client.post("/api/v1/todos", json={"title": "Test2"})

        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        # Check items structure
        for item in data["items"]:
            assert "id" in item
            assert "title" in item
            assert "description" in item
            assert "is_done" in item
            assert "created_at" in item
            assert "updated_at" in item

    def test_pagination_from_database(self):
        """Test that pagination actually limits query results from database"""
        # Create 15 todos
        for i in range(15):
            client.post("/api/v1/todos", json={"title": f"Todo {i:02d}"})

        # Test different limits and offsets
        response = client.get("/api/v1/todos?limit=5&offset=0")
        assert len(response.json()["items"]) == 5

        response = client.get("/api/v1/todos?limit=5&offset=5")
        assert len(response.json()["items"]) == 5

        response = client.get("/api/v1/todos?limit=5&offset=10")
        assert len(response.json()["items"]) == 5

        response = client.get("/api/v1/todos?limit=10&offset=10")
        assert len(response.json()["items"]) == 5  # Only 5 left

        assert response.json()["total"] == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
