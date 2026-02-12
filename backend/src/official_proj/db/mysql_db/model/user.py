from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(
        index=True,
        unique=True,
        max_length=50
    )
    password: str = Field(max_length=100)  # ⚠️ 明文
    created_at: datetime = Field(default_factory=datetime.utcnow)
