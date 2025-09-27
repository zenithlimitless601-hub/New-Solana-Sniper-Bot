from datetime import datetime
from typing import Optional
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Analysis(SQLModel, table=True):
    __tablename__ = "analyses"
    id: Optional[int] = Field(default=None, primary_key=True)
    token_id: int = Field(foreign_key="tokens.id", index=True)
    score: float
    is_scam: bool
    details: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB().with_variant(SQLITE_JSON, "sqlite"))
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
