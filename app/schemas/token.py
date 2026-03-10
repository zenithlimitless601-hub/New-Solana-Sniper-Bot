"""Token request/response schemas."""

from pydantic import BaseModel, Field


class TokenIn(BaseModel):
    """Input schema for submitting a token for analysis or trading."""

    address: str
    symbol: str | None = None
    name: str | None = None
    liquidity: float | None = None
    volume_24h: float | None = None
    extras: dict | None = None


class TokenOut(TokenIn):
    """Output schema with database ID included."""

    id: int = Field(...)
