import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrderNotFoundError, PizzaNotFoundError
from app.crud import order as order_crud
from app.crud import pizza as pizza_crud
from app.models.order import Order
from app.schemas.enums import OrderStatus
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate

logger = logging.getLogger(__name__)


async def _get_or_404(db: AsyncSession, order_id: int) -> Order:
    order = await order_crud.get_order(db, order_id)
    if order is None:
        raise OrderNotFoundError()
    return order


async def create_order(db: AsyncSession, payload: OrderCreate) -> OrderRead:
    pizza = await pizza_crud.get_pizza(db, payload.pizza_id)
    if pizza is None:
        raise PizzaNotFoundError()
    order = await order_crud.create_order(
        db,
        {
            **payload.model_dump(),
            "pizza_name": pizza.name,
            "status": OrderStatus.preparing.value,
            "total_price": pizza.price * payload.quantity,
        },
    )
    return OrderRead.model_validate(order)


async def get_order(db: AsyncSession, order_id: int) -> OrderRead:
    return OrderRead.model_validate(await _get_or_404(db, order_id))


async def list_orders(db: AsyncSession, *, limit: int, offset: int) -> list[OrderRead]:
    orders = await order_crud.list_orders(db, limit=limit, offset=offset)
    return [OrderRead.model_validate(order) for order in orders]


async def update_order(db: AsyncSession, order_id: int, payload: OrderUpdate) -> OrderRead:
    order = await _get_or_404(db, order_id)
    order = await order_crud.update_order(db, order, {"status": payload.status.value})
    return OrderRead.model_validate(order)


def notify_kitchen(order_id: int) -> None:
    """Runs after the response is sent (see BackgroundTasks in the route)."""
    logger.info("👨‍🍳 Kitchen notified: order #%s is on the board!", order_id)
