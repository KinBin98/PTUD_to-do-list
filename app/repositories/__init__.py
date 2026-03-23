from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date
from app.core.models import Todo, User


class UserRepository:
    """Repository for managing users"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, email: str, hashed_password: str) -> User:
        """Create a new user"""
        db_user = User(email=email, hashed_password=hashed_password)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self) -> List[User]:
        """Get all users"""
        return self.db.query(User).all()


class TodoRepository:
    """Repository for managing todos with SQLAlchemy"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, description: Optional[str], is_done: bool, owner_id: int, 
               due_date: Optional[datetime] = None, tags: Optional[List[str]] = None) -> Todo:
        """Create a new todo"""
        db_todo = Todo(
            title=title, 
            description=description, 
            is_done=is_done, 
            owner_id=owner_id,
            due_date=due_date,
            tags=tags or []
        )
        self.db.add(db_todo)
        self.db.commit()
        self.db.refresh(db_todo)
        return db_todo

    def get_all(self, user_id: int) -> List[Todo]:
        """Get all todos for a user"""
        return self.db.query(Todo).filter(Todo.owner_id == user_id).all()

    def get_by_id(self, todo_id: int, user_id: int) -> Optional[Todo]:
        """Get a todo by ID (check ownership)"""
        return self.db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.owner_id == user_id
        ).first()

    def update(self, todo_id: int, user_id: int, title: Optional[str] = None, 
               description: Optional[str] = None, is_done: Optional[bool] = None,
               due_date: Optional[datetime] = None, tags: Optional[List[str]] = None) -> Optional[Todo]:
        """Update a todo (check ownership)"""
        db_todo = self.get_by_id(todo_id, user_id)
        if not db_todo:
            return None
        if title is not None:
            db_todo.title = title
        if description is not None:
            db_todo.description = description
        if is_done is not None:
            db_todo.is_done = is_done
        if due_date is not None:
            db_todo.due_date = due_date
        if tags is not None:
            db_todo.tags = tags
        self.db.commit()
        self.db.refresh(db_todo)
        return db_todo

    def delete(self, todo_id: int, user_id: int) -> bool:
        """Delete a todo (check ownership)"""
        db_todo = self.get_by_id(todo_id, user_id)
        if not db_todo:
            return False
        self.db.delete(db_todo)
        self.db.commit()
        return True

    def get_filtered(
        self,
        user_id: int,
        q: Optional[str] = None,
        is_done: Optional[bool] = None,
        sort: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ):
        """Get todos for user with filtering, searching, sorting and pagination"""
        query = self.db.query(Todo).filter(Todo.owner_id == user_id)

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

    def get_overdue(self, user_id: int) -> List[Todo]:
        """Get overdue todos (due_date < today) and not done"""
        today = datetime.now().date()
        return self.db.query(Todo).filter(
            and_(
                Todo.owner_id == user_id,
                Todo.due_date < datetime.combine(today, datetime.min.time()),
                Todo.is_done == False
            )
        ).order_by(Todo.due_date).all()

    def get_today(self, user_id: int) -> List[Todo]:
        """Get todos due today and not done"""
        today = datetime.now().date()
        tomorrow = datetime.combine(today, datetime.min.time())
        end_of_today = datetime.combine(today, datetime.max.time())
        
        return self.db.query(Todo).filter(
            and_(
                Todo.owner_id == user_id,
                Todo.due_date >= tomorrow,
                Todo.due_date <= end_of_today,
                Todo.is_done == False
            )
        ).order_by(Todo.due_date).all()
