"""Token ORM model -- represents a Solana token tracked by the bot."""

from datetime import datetime, timezone

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlmodel import Field, SQLModel


class Token(SQLModel, table=True):
    """Solana token stored in the database."""

    __tablename__ = "tokens"

    id: int | None = Field(default=None, primary_key=True)
    address: str = Field(unique=True, index=True)
    symbol: str | None = None
    name: str | None = None
    liquidity: float | None = None
    volume_24h: float | None = None
    extras: dict | None = Field(
        default=None,
        sa_column=Column(JSONB().with_variant(SQLITE_JSON, "sqlite")),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
