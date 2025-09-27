from pydantic import BaseModel


class ProcessResultOut(BaseModel):
    token_id: int
    opened_trade_id: int | None
    analysis: dict
