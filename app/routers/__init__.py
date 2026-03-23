from fastapi import APIRouter, HTTPException, Query, Depends, status, Header
from typing import Optional
from sqlalchemy.orm import Session
from app.schemas import (
    TodoCreate, TodoUpdate, Todo, TodoListResponse,
    UserRegister, UserLogin, UserResponse, TokenResponse
)
from app.services import TodoService, AuthService
from app.core.database import get_db

# Create auth router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Create todos router
todos_router = APIRouter(prefix="/todos", tags=["todos"])


# ===== Helper: Get current user from token =====
async def get_current_user_id(authorization: Optional[str] = None) -> int:
    """Extract user_id from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    # Verify token (we'll use a temporary auth service for this)
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        user_id = auth_service.verify_token(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_id
    finally:
        db.close()


# ===== Auth Endpoints =====
@auth_router.post("/register", response_model=UserResponse)
def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    service = AuthService(db)
    try:
        new_user = service.create_user(user.email, user.password)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    service = AuthService(db)
    db_user = service.authenticate_user(user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = service.create_access_token(db_user.id)
    return {"access_token": access_token}


@auth_router.get("/me", response_model=UserResponse)
def get_me(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Get current user info"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = AuthService(db)
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user_id = service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# ===== Todo Endpoints =====
@todos_router.post("", response_model=Todo)
def create_todo(
    todo: TodoCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new todo"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = TodoService(db)
    auth_service = AuthService(db)
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user_id = auth_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = service.create_todo(todo.title, todo.description, todo.is_done, user_id)
    return result


@todos_router.get("", response_model=TodoListResponse)
def get_todos(
    q: Optional[str] = Query(None, description="Search by title"),
    is_done: Optional[bool] = Query(None, description="Filter by completion status"),
    sort: Optional[str] = Query(None, description="Sort by field"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get user's todos with filtering, searching, sorting and pagination"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = TodoService(db)
    auth_service = AuthService(db)
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user_id = auth_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return service.get_todos(user_id, q, is_done, sort, limit, offset)


@todos_router.get("/{todo_id}", response_model=Todo)
def get_todo(
    todo_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get a specific todo by ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = TodoService(db)
    auth_service = AuthService(db)
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user_id = auth_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    todo = service.get_todo_by_id(todo_id, user_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@todos_router.put("/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    todo: TodoCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Update a todo completely"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = TodoService(db)
    auth_service = AuthService(db)
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user_id = auth_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = service.update_todo(todo_id, user_id, todo.title, todo.description, todo.is_done)
    if not result:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@todos_router.patch("/{todo_id}", response_model=Todo)
def partial_update_todo(
    todo_id: int,
    todo: TodoUpdate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Update a todo partially (PATCH)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = TodoService(db)
    auth_service = AuthService(db)
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user_id = auth_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = service.update_todo(
        todo_id,
        user_id,
        title=todo.title,
        description=todo.description,
        is_done=todo.is_done
    )
    if not result:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@todos_router.delete("/{todo_id}")
def delete_todo(
    todo_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a todo"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = TodoService(db)
    auth_service = AuthService(db)
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user_id = auth_service.verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    success = service.delete_todo(todo_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted"}


# Create main router
router = APIRouter(prefix="", tags=[""])
router.include_router(auth_router)
router.include_router(todos_router)
