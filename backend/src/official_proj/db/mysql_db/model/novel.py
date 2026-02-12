# official_proj/db/models/novel.py
from sqlmodel import SQLModel, Field


class Novel(SQLModel, table=True):
    __tablename__ = "novels"

    novel_id: str = Field(primary_key=True, index=True)
    topic: str
    user_id: int = Field(index=True)
