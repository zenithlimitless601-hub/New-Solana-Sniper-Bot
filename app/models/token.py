from datetime import datetime
from typing import Optional
from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Token(SQLModel, table=True):
    __tablename__ = "tokens"
    id: Optional[int] = Field(default=None, primary_key=True)
    address: str = Field(unique=True, index=True)
    symbol: Optional[str] = None
    name: Optional[str] = None
    liquidity: Optional[float] = None
    volume_24h: Optional[float] = None
    extras: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB().with_variant(SQLITE_JSON, "sqlite"))
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
