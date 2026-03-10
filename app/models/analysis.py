"""Analysis ORM model -- risk assessment result for a token."""

from datetime import datetime, timezone

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlmodel import Field, SQLModel


class Analysis(SQLModel, table=True):
    """Token risk analysis record."""

    __tablename__ = "analyses"

    id: int | None = Field(default=None, primary_key=True)
    token_id: int = Field(foreign_key="tokens.id", index=True)
    score: float
    is_scam: bool
    details: dict | None = Field(
        default=None,
        sa_column=Column(JSONB().with_variant(SQLITE_JSON, "sqlite")),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
