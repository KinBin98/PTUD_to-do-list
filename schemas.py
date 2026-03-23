from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class TodoBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    is_done: bool = False


class TodoCreate(TodoBase):
    pass


class Todo(TodoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TodoInDB(Todo):
    created_at: datetime


class TodoListResponse(BaseModel):
    items: list[Todo]
    total: int
    limit: int
    offset: int
