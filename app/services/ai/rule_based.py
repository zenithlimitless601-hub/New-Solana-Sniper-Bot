from app.schemas.analysis import AnalysisOut
from app.schemas.token import TokenIn
from app.services.ai.base import Analyzer


class RuleBasedAnalyzer(Analyzer):
    async def assess(self, token: TokenIn) -> AnalysisOut:
        name = (token.name or "").lower()
        symbol = (token.symbol or "").lower()
        md = token.extras or {}
        socials = ["twitter", "telegram", "website"]
        score = 0.5
        for k in socials:
            if md.get(k):
                score += 0.1
        bad = ["rug", "scam", "honeypot"]
        for w in bad:
            if w in name or w in symbol:
                score -= 0.3
        score = max(0.0, min(1.0, score))
        is_scam = score < 0.4
        return AnalysisOut(score=score, is_scam=is_scam, details={"socials": md})
