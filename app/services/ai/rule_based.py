"""Rule-based token analyzer with heuristic scoring."""

from app.schemas.analysis import AnalysisOut
from app.schemas.token import TokenIn
from app.services.ai.base import Analyzer

_SOCIAL_KEYS = ("twitter", "telegram", "website")
_SCAM_KEYWORDS = ("rug", "scam", "honeypot")
_SOCIAL_BONUS = 0.1
_SCAM_PENALTY = 0.3
_BASE_SCORE = 0.5
_SCAM_THRESHOLD = 0.4


class RuleBasedAnalyzer(Analyzer):
    """Scores tokens using simple heuristics: social presence and name checks.

    Scoring logic:
        - Base score: 0.5
        - +0.1 per social link found (twitter, telegram, website)
        - -0.3 per scam keyword in name/symbol (rug, scam, honeypot)
        - Clamped to [0.0, 1.0]; flagged as scam if score < 0.4
    """

    async def assess(self, token: TokenIn) -> AnalysisOut:
        """Evaluate token risk based on metadata heuristics."""
        name = (token.name or "").lower()
        symbol = (token.symbol or "").lower()
        extras = token.extras or {}

        score = _BASE_SCORE
        for key in _SOCIAL_KEYS:
            if extras.get(key):
                score += _SOCIAL_BONUS
        for keyword in _SCAM_KEYWORDS:
            if keyword in name or keyword in symbol:
                score -= _SCAM_PENALTY

        score = max(0.0, min(1.0, score))
        is_scam = score < _SCAM_THRESHOLD
        return AnalysisOut(score=score, is_scam=is_scam, details={"socials": extras})
