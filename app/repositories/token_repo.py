from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Token


class TokenRepo:
    async def get_by_address(self, session: AsyncSession, address: str) -> Optional[Token]:
        res = await session.execute(select(Token).where(Token.address == address))
        return res.scalar_one_or_none()

    async def create_or_update(self, session: AsyncSession, data: dict) -> tuple[Token, bool]:
        token = await self.get_by_address(session, data["address"])
        if token:
            for k, v in data.items():
                setattr(token, k, v)
            await session.flush()
            return token, False
        token = Token(**data)
        session.add(token)
        await session.flush()
        return token, True

    async def list_tokens(self, session: AsyncSession, limit: int = 50, offset: int = 0) -> list[Token]:
        res = await session.execute(select(Token).order_by(Token.id.desc()).limit(limit).offset(offset))
        return list(res.scalars().all())
