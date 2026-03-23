from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.schemas import TodoCreate, TodoUpdate, Todo, TodoListResponse
from app.services import TodoService
from app.core.database import get_db

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=Todo)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo"""
    service = TodoService(db)
    result = service.create_todo(todo.title, todo.description, todo.is_done)
    return result


@router.get("", response_model=TodoListResponse)
def get_todos(
    q: Optional[str] = Query(None, description="Search by title"),
    is_done: Optional[bool] = Query(None, description="Filter by completion status"),
    sort: Optional[str] = Query(None, description="Sort by field"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all todos with filtering, searching, sorting and pagination"""
    service = TodoService(db)
    return service.get_todos(q, is_done, sort, limit, offset)


@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a specific todo by ID"""
    service = TodoService(db)
    todo = service.get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    """Update a todo completely"""
    service = TodoService(db)
    result = service.update_todo(todo_id, todo.title, todo.description, todo.is_done)
    if not result:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@router.patch("/{todo_id}", response_model=Todo)
def partial_update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    """Update a todo partially (PATCH)"""
    service = TodoService(db)
    result = service.update_todo(
        todo_id,
        title=todo.title,
        description=todo.description,
        is_done=todo.is_done
    )
    if not result:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@router.delete("/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo"""
    service = TodoService(db)
    success = service.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted"}
