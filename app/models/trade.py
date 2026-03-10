"""Trade ORM model -- represents a simulated or real trade."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Trade(SQLModel, table=True):
    """Individual trade record with entry/exit data and PnL."""

    __tablename__ = "trades"

    id: int | None = Field(default=None, primary_key=True)
    token_id: int = Field(foreign_key="tokens.id", index=True)
    mode: str = Field(default="simulation", index=True)
    status: str = Field(default="open", index=True)
    entry_price: float
    entry_amount_usd: float
    entry_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    exit_price: float | None = None
    exit_time: datetime | None = None
    roi: float | None = None
    pnl_usd: float | None = None
