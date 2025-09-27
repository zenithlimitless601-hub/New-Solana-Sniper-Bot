from pydantic import BaseModel


class AnalysisOut(BaseModel):
    score: float
    is_scam: bool
    details: dict | None = None
