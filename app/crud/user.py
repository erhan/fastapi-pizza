from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email))


async def create_user(db: AsyncSession, data: dict[str, Any]) -> User:
    user = User(**data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
