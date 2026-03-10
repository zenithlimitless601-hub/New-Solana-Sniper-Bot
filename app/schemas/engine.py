"""Engine pipeline result schema."""

from pydantic import BaseModel


class ProcessResultOut(BaseModel):
    """Result of the analyze-and-trade pipeline."""

    token_id: int
    opened_trade_id: int | None
    analysis: dict
