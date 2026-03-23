from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.models import Todo
from app.core.database import SessionLocal


class TodoRepository:
    """Repository for managing todos with SQLAlchemy"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, description: Optional[str] = None, is_done: bool = False) -> Todo:
        """Create a new todo"""
        db_todo = Todo(title=title, description=description, is_done=is_done)
        self.db.add(db_todo)
        self.db.commit()
        self.db.refresh(db_todo)
        return db_todo

    def get_all(self) -> List[Todo]:
        """Get all todos"""
        return self.db.query(Todo).all()

    def get_by_id(self, todo_id: int) -> Optional[Todo]:
        """Get a todo by ID"""
        return self.db.query(Todo).filter(Todo.id == todo_id).first()

    def update(self, todo_id: int, title: Optional[str] = None, description: Optional[str] = None, is_done: Optional[bool] = None) -> Optional[Todo]:
        """Update a todo"""
        db_todo = self.get_by_id(todo_id)
        if not db_todo:
            return None
        if title is not None:
            db_todo.title = title
        if description is not None:
            db_todo.description = description
        if is_done is not None:
            db_todo.is_done = is_done
        self.db.commit()
        self.db.refresh(db_todo)
        return db_todo

    def delete(self, todo_id: int) -> bool:
        """Delete a todo"""
        db_todo = self.get_by_id(todo_id)
        if not db_todo:
            return False
        self.db.delete(db_todo)
        self.db.commit()
        return True

    def get_filtered(
        self,
        q: Optional[str] = None,
        is_done: Optional[bool] = None,
        sort: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ):
        """Get todos with filtering, searching, sorting and pagination"""
        query = self.db.query(Todo)

        # Filter by is_done
        if is_done is not None:
            query = query.filter(Todo.is_done == is_done)

        # Search by title
        if q:
            query = query.filter(Todo.title.ilike(f"%{q}%"))

        # Sort
        if sort:
            reverse = sort.startswith("-")
            field = sort.lstrip("-")
            if hasattr(Todo, field):
                column = getattr(Todo, field)
                query = query.order_by(column.desc() if reverse else column)

        # Get total before pagination
        total = query.count()

        # Apply pagination
        items = query.limit(limit).offset(offset).all()

        return items, total
