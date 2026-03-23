from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.repositories import TodoRepository, UserRepository
from app.schemas import TodoListResponse
from app.core.config import settings
from app.core.models import User

# Password hashing - use pbkdf2_sha256 for better compatibility
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


class AuthService:
    """Service for user authentication"""

    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.db = db

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, email: str, password: str) -> User:
        """Create a new user"""
        # Check if user exists
        if self.repository.get_by_email(email):
            raise ValueError("Email already registered")
        
        hashed_password = self.hash_password(password)
        return self.repository.create(email, hashed_password)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = self.repository.get_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[int]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return int(user_id)
        except JWTError:
            return None

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.repository.get_by_id(user_id)


class TodoService:
    """Service for todo business logic"""

    def __init__(self, db: Session):
        self.repository = TodoRepository(db)
        self.db = db

    def create_todo(self, title: str, description: Optional[str], is_done: bool, user_id: int,
                    due_date: Optional[datetime] = None, tags: Optional[List[str]] = None):
        """Create a new todo"""
        todo = self.repository.create(title, description, is_done, user_id, due_date, tags)
        return todo

    def get_todos(
        self,
        user_id: int,
        q: Optional[str] = None,
        is_done: Optional[bool] = None,
        sort: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> TodoListResponse:
        """Get todos with filtering, searching, sorting and pagination"""
        items, total = self.repository.get_filtered(user_id, q, is_done, sort, limit, offset)

        return TodoListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )

    def get_todo_by_id(self, todo_id: int, user_id: int):
        """Get a todo by ID"""
        return self.repository.get_by_id(todo_id, user_id)

    def update_todo(self, todo_id: int, user_id: int, title: Optional[str] = None, 
                    description: Optional[str] = None, is_done: Optional[bool] = None,
                    due_date: Optional[datetime] = None, tags: Optional[List[str]] = None):
        """Update a todo"""
        return self.repository.update(todo_id, user_id, title, description, is_done, due_date, tags)

    def delete_todo(self, todo_id: int, user_id: int) -> bool:
        """Soft delete a todo"""
        return self.repository.delete(todo_id, user_id)

    def restore_todo(self, todo_id: int, user_id: int):
        """Restore a soft-deleted todo"""
        return self.repository.restore(todo_id, user_id)

    def hard_delete_todo(self, todo_id: int, user_id: int) -> bool:
        """Permanently delete a todo"""
        return self.repository.hard_delete(todo_id, user_id)

    def get_deleted_todos(self, user_id: int) -> List:
        """Get soft-deleted todos"""
        return self.repository.get_deleted(user_id)

    def get_overdue_todos(self, user_id: int) -> List:
        """Get overdue todos"""
        return self.repository.get_overdue(user_id)

    def get_today_todos(self, user_id: int) -> List:
        """Get todos due today"""
        return self.repository.get_today(user_id)
