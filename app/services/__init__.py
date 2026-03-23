from typing import Optional
from sqlalchemy.orm import Session
from app.repositories import TodoRepository
from app.schemas import TodoListResponse


class TodoService:
    """Service for todo business logic"""

    def __init__(self, db: Session):
        self.repository = TodoRepository(db)
        self.db = db

    def create_todo(self, title: str, description: Optional[str] = None, is_done: bool = False) -> dict:
        """Create a new todo"""
        todo = self.repository.create(title, description, is_done)
        return todo

    def get_todos(
        self,
        q: Optional[str] = None,
        is_done: Optional[bool] = None,
        sort: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> TodoListResponse:
        """Get todos with filtering, searching, sorting and pagination"""
        items, total = self.repository.get_filtered(q, is_done, sort, limit, offset)

        return TodoListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )

    def get_todo_by_id(self, todo_id: int) -> Optional[dict]:
        """Get a todo by ID"""
        return self.repository.get_by_id(todo_id)

    def update_todo(self, todo_id: int, title: Optional[str] = None, description: Optional[str] = None, is_done: Optional[bool] = None) -> Optional[dict]:
        """Update a todo"""
        return self.repository.update(todo_id, title, description, is_done)

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo"""
        return self.repository.delete(todo_id)
