from abc import ABC, abstractmethod
from app.schemas.analysis import AnalysisOut
from app.schemas.token import TokenIn


class Analyzer(ABC):
    @abstractmethod
    async def assess(self, token: TokenIn) -> AnalysisOut: ...
