from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pizza import Pizza


async def get_pizza(db: AsyncSession, pizza_id: int) -> Pizza | None:
    return await db.get(Pizza, pizza_id)


async def list_pizzas(
    db: AsyncSession,
    *,
    vegetarian: bool | None,
    max_price: int | None,
    limit: int,
    offset: int,
) -> list[Pizza]:
    statement = select(Pizza).order_by(Pizza.id).limit(limit).offset(offset)
    if vegetarian is not None:
        statement = statement.where(Pizza.is_vegetarian == vegetarian)
    if max_price is not None:
        statement = statement.where(Pizza.price <= max_price)
    return list(await db.scalars(statement))


async def count_pizzas(db: AsyncSession) -> int:
    return await db.scalar(select(func.count(Pizza.id))) or 0


async def create_pizza(db: AsyncSession, data: dict[str, Any]) -> Pizza:
    pizza = Pizza(**data)
    db.add(pizza)
    await db.commit()
    await db.refresh(pizza)
    return pizza


async def update_pizza(db: AsyncSession, pizza: Pizza, data: dict[str, Any]) -> Pizza:
    for field, value in data.items():
        setattr(pizza, field, value)
    await db.commit()
    await db.refresh(pizza)
    return pizza


async def delete_pizza(db: AsyncSession, pizza: Pizza) -> None:
    await db.delete(pizza)
    await db.commit()
