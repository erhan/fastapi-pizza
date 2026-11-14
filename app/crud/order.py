from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


async def get_order(db: AsyncSession, order_id: int) -> Order | None:
    return await db.get(Order, order_id)


async def list_orders(
    db: AsyncSession, *, limit: int, offset: int, user_id: int | None = None
) -> list[Order]:
    statement = select(Order).order_by(Order.id).limit(limit).offset(offset)
    if user_id is not None:
        statement = statement.where(Order.user_id == user_id)
    return list(await db.scalars(statement))


async def has_orders_for_pizza(db: AsyncSession, pizza_id: int) -> bool:
    statement = select(select(Order.id).where(Order.pizza_id == pizza_id).exists())
    return bool(await db.scalar(statement))


async def create_order(db: AsyncSession, data: dict[str, Any]) -> Order:
    order = Order(**data)
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def update_order(db: AsyncSession, order: Order, data: dict[str, Any]) -> Order:
    for field, value in data.items():
        setattr(order, field, value)
    await db.commit()
    await db.refresh(order)
    return order
