from pydantic import BaseModel, Field


class TokenIn(BaseModel):
    address: str
    symbol: str | None = None
    name: str | None = None
    liquidity: float | None = None
    volume_24h: float | None = None
    extras: dict | None = None


class TokenOut(TokenIn):
    id: int = Field(...)
