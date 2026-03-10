"""Repository for Analysis CRUD operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Analysis


class AnalysisRepo:
    """Data-access layer for the analyses table."""

    async def create(self, session: AsyncSession, data: dict) -> Analysis:
        """Persist a new analysis record."""
        analysis = Analysis(**data)
        session.add(analysis)
        await session.flush()
        return analysis

    async def latest_for_token(
        self, session: AsyncSession, token_id: int
    ) -> Analysis | None:
        """Return the most recent analysis for a given token."""
        res = await session.execute(
            select(Analysis)
            .where(Analysis.token_id == token_id)
            .order_by(Analysis.id.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()
