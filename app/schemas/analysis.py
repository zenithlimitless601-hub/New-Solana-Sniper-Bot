"""Analysis response schema."""

from pydantic import BaseModel


class AnalysisOut(BaseModel):
    """Risk analysis result with score and scam flag."""

    score: float
    is_scam: bool
    details: dict | None = None
