"""Abstract base class for token analyzers."""

from abc import ABC, abstractmethod

from app.schemas.analysis import AnalysisOut
from app.schemas.token import TokenIn


class Analyzer(ABC):
    """Interface for token risk-assessment backends."""

    @abstractmethod
    async def assess(self, token: TokenIn) -> AnalysisOut:
        """Analyze a token and return a risk score with scam flag."""
        ...
