from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.deps import DbSession, PageParams, require_api_key
from app.schemas.common import NOT_FOUND, UNAUTHORIZED
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate
from app.services import order as order_service

router = APIRouter()


@router.post("", status_code=201, summary="Order a pizza", responses=NOT_FOUND)
async def create_order(
    payload: OrderCreate, db: DbSession, background_tasks: BackgroundTasks
) -> OrderRead:
    order = await order_service.create_order(db, payload)
    background_tasks.add_task(order_service.notify_kitchen, order.id)
    return order


@router.get("", summary="List orders")
async def list_orders(db: DbSession, page: PageParams) -> list[OrderRead]:
    return await order_service.list_orders(db, limit=page.limit, offset=page.offset)


@router.get("/{order_id}", summary="Follow an order", responses=NOT_FOUND)
async def get_order(order_id: int, db: DbSession) -> OrderRead:
    return await order_service.get_order(db, order_id)


@router.patch(
    "/{order_id}",
    summary="Move an order along",
    dependencies=[Depends(require_api_key)],
    responses=UNAUTHORIZED | NOT_FOUND,
)
async def update_order(order_id: int, payload: OrderUpdate, db: DbSession) -> OrderRead:
    return await order_service.update_order(db, order_id, payload)
