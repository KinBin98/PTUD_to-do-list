"""
Test suite for To-Do List API (Levels 2-5)
Tests validation, filtering/sorting/pagination, layered architecture, database operations, and authentication
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db
from app.core.models import Todo, User
from app.services import AuthService


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


# ===== Helper Functions =====
def create_test_user(email: str = "test@example.com", password: str = "testpass123"):
    """Create a test user and return (user, token)"""
    db = TestingSessionLocal()
    auth_service = AuthService(db)
    user = auth_service.create_user(email, password)
    token = auth_service.create_access_token(user.id)
    db.close()
    return user, token


def get_auth_header(token: str) -> dict:
    """Get authorization header"""
    return {"Authorization": f"Bearer {token}"}


# ===== Cấp 5 - Authentication Tests =====
class TestAuthentication:
    """Test Level 5 - Authentication"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup clean database"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_register_valid(self):
        """Test user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "john@example.com", "password": "securepass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "john@example.com"
        assert "id" in data
        assert data["is_active"] is True

    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "securepass123"}
        )
        assert response.status_code == 422

    def test_register_password_too_short(self):
        """Test registration with password < 8 chars"""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "jane@example.com", "password": "short"}
        )
        assert response.status_code == 422

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # First registration
        client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "securepass123"}
        )
        
        # Second registration with same email
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "anotherpass123"}
        )
        assert response.status_code == 400

    def test_login_valid(self):
        """Test user login"""
        # Register
        client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "securepass123"}
        )
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "securepass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "securepass123"}
        )
        assert response.status_code == 401

    def test_login_invalid_password(self):
        """Test login with wrong password"""
        # Register
        client.post(
            "/api/v1/auth/register",
            json={"email": "pwd@example.com", "password": "correctpass123"}
        )
        
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "pwd@example.com", "password": "wrongpass123"}
        )
        assert response.status_code == 401

    def test_get_me(self):
        """Test getting current user info"""
        user, token = create_test_user()
        
        response = client.get(
            "/api/v1/auth/me",
            headers=get_auth_header(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email

    def test_get_me_no_token(self):
        """Test get_me without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self):
        """Test get_me with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


# ===== Cấp 2 - Validation (Updated for Auth) =====
class TestValidation:
    """Test Level 2 - Validation"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup with test user"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.user, self.token = create_test_user()
        self.headers = get_auth_header(self.token)

    def test_create_todo_valid(self):
        """Test creating a valid todo"""
        response = client.post(
            "/api/v1/todos",
            headers=self.headers,
            json={"title": "Test Todo", "description": "A test todo"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["owner_id"] == self.user.id

    def test_title_too_short(self):
        """Title must be at least 3 characters"""
        response = client.post(
            "/api/v1/todos",
            headers=self.headers,
            json={"title": "ab"}
        )
        assert response.status_code == 422

    def test_title_too_long(self):
        """Title must not exceed 100 characters"""
        long_title = "a" * 101
        response = client.post(
            "/api/v1/todos",
            headers=self.headers,
            json={"title": long_title}
        )
        assert response.status_code == 422

    def test_create_todo_without_auth(self):
        """Test creating todo without authentication"""
        response = client.post(
            "/api/v1/todos",
            json={"title": "Test Todo"}
        )
        assert response.status_code == 401


# ===== Cấp 2 - Filter/Search/Sort/Pagination (Updated for Auth) =====
class TestFilterSearchSort:
    """Test Level 2 - Filter, Search, Sort, Pagination"""

    @pytest.fixture(autouse=True)
    def setup_todos(self):
        """Create sample todos for testing"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        self.user, self.token = create_test_user()
        self.headers = get_auth_header(self.token)
        
        # Create test data
        todos_data = [
            {"title": "Buy groceries", "is_done": True},
            {"title": "Read documentation", "is_done": False},
            {"title": "Write tests", "is_done": False},
            {"title": "Deploy application", "is_done": True},
            {"title": "Code review", "is_done": False},
        ]
        
        for todo in todos_data:
            client.post(
                "/api/v1/todos",
                headers=self.headers,
                json=todo
            )

    def test_get_all_todos(self):
        """Test getting all todos"""
        response = client.get(
            "/api/v1/todos",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    def test_filter_by_is_done_true(self):
        """Test filtering by is_done=true"""
        response = client.get(
            "/api/v1/todos?is_done=true",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["is_done"] is True

    def test_search_by_keyword(self):
        """Test searching by keyword"""
        response = client.get(
            "/api/v1/todos?q=review",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_sort_by_created_at_descending(self):
        """Test sorting by created_at descending"""
        response = client.get(
            "/api/v1/todos?sort=-created_at",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        for i in range(len(items) - 1):
            assert items[i]["created_at"] >= items[i + 1]["created_at"]

    def test_pagination_limit(self):
        """Test pagination limit parameter"""
        response = client.get(
            "/api/v1/todos?limit=2",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5


# ===== Cấp 4 - Database Operations (Updated for Auth) =====
class TestDatabase:
    """Test Level 4 - Database Operations"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup clean database"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.user, self.token = create_test_user()
        self.headers = get_auth_header(self.token)

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set"""
        response = client.post(
            "/api/v1/todos",
            headers=self.headers,
            json={"title": "Auto Timestamp"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "created_at" in data

    def test_updated_at_auto_set(self):
        """Test that updated_at is automatically set"""
        response = client.post(
            "/api/v1/todos",
            headers=self.headers,
            json={"title": "Auto Timestamp"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "updated_at" in data

    def test_patch_partial_update(self):
        """Test PATCH endpoint for partial updates"""
        create_response = client.post(
            "/api/v1/todos",
            headers=self.headers,
            json={"title": "Original", "is_done": False}
        )
        todo_id = create_response.json()["id"]

        patch_response = client.patch(
            f"/api/v1/todos/{todo_id}",
            headers=self.headers,
            json={"is_done": True}
        )
        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["is_done"] is True
        assert data["title"] == "Original"

    def test_get_nonexistent_todo(self):
        """Test getting a non-existent todo returns 404"""
        response = client.get(
            "/api/v1/todos/99999",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_update_nonexistent_todo(self):
        """Test updating a non-existent todo returns 404"""
        response = client.put(
            "/api/v1/todos/99999",
            headers=self.headers,
            json={"title": "New"}
        )
        assert response.status_code == 404

    def test_delete_nonexistent_todo(self):
        """Test deleting a non-existent todo returns 404"""
        response = client.delete(
            "/api/v1/todos/99999",
            headers=self.headers
        )
        assert response.status_code == 404


# ===== Cấp 5 - User Ownership Tests =====
class TestUserOwnership:
    """Test Level 5 - User Ownership"""

    @pytest.fixture(autouse=True)
    def setup_users(self):
        """Setup two test users"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        self.user1, self.token1 = create_test_user("user1@example.com")
        self.user2, self.token2 = create_test_user("user2@example.com")
        self.headers1 = get_auth_header(self.token1)
        self.headers2 = get_auth_header(self.token2)

    def test_user_can_only_see_own_todos(self):
        """Test that user can only see their own todos"""
        # User 1 creates a todo
        client.post(
            "/api/v1/todos",
            headers=self.headers1,
            json={"title": "User1 Todo"}
        )
        
        # User 2 creates a todo
        client.post(
            "/api/v1/todos",
            headers=self.headers2,
            json={"title": "User2 Todo"}
        )
        
        # User 1 should only see 1 todo
        response1 = client.get("/api/v1/todos", headers=self.headers1)
        assert response1.json()["total"] == 1
        assert response1.json()["items"][0]["title"] == "User1 Todo"
        
        # User 2 should only see 1 todo
        response2 = client.get("/api/v1/todos", headers=self.headers2)
        assert response2.json()["total"] == 1
        assert response2.json()["items"][0]["title"] == "User2 Todo"

    def test_user_cannot_see_other_users_todo(self):
        """Test that user cannot access other user's todo"""
        # User 1 creates a todo
        create_response = client.post(
            "/api/v1/todos",
            headers=self.headers1,
            json={"title": "User1 Private Todo"}
        )
        todo_id = create_response.json()["id"]
        
        # User 2 tries to get User 1's todo
        response = client.get(
            f"/api/v1/todos/{todo_id}",
            headers=self.headers2
        )
        assert response.status_code == 404

    def test_user_cannot_delete_other_users_todo(self):
        """Test that user cannot delete other user's todo"""
        # User 1 creates a todo
        create_response = client.post(
            "/api/v1/todos",
            headers=self.headers1,
            json={"title": "User1 Todo"}
        )
        todo_id = create_response.json()["id"]
        
        # User 2 tries to delete User 1's todo
        response = client.delete(
            f"/api/v1/todos/{todo_id}",
            headers=self.headers2
        )
        assert response.status_code == 404
        
        # Verify User 1's todo still exists
        get_response = client.get(
            f"/api/v1/todos/{todo_id}",
            headers=self.headers1
        )
        assert get_response.status_code == 200

    def test_user_cannot_update_other_users_todo(self):
        """Test that user cannot update other user's todo"""
        # User 1 creates a todo
        create_response = client.post(
            "/api/v1/todos",
            headers=self.headers1,
            json={"title": "User1 Todo"}
        )
        todo_id = create_response.json()["id"]
        
        # User 2 tries to update User 1's todo
        response = client.patch(
            f"/api/v1/todos/{todo_id}",
            headers=self.headers2,
            json={"title": "Hacked!"}
        )
        assert response.status_code == 404
        
        # Verify User 1's todo is unchanged
        get_response = client.get(
            f"/api/v1/todos/{todo_id}",
            headers=self.headers1
        )
        assert get_response.json()["title"] == "User1 Todo"

    def test_password_hashing(self):
        """Test that passwords are hashed"""
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "user1@example.com").first()
        
        # Password should be hashed, not plain text
        assert user.hashed_password != "testpass123"
        assert len(user.hashed_password) > 20  # bcrypt hashes are long
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
