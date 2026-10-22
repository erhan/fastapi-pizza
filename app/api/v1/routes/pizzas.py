from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, PageParams, require_api_key
from app.schemas.common import CONFLICT, NOT_FOUND, UNAUTHORIZED
from app.schemas.pizza import PizzaCreate, PizzaRead, PizzaUpdate
from app.services import pizza as pizza_service

router = APIRouter()


@router.get("", summary="Browse the menu")
async def list_pizzas(
    db: DbSession,
    page: PageParams,
    vegetarian: Annotated[bool | None, Query(description="Only (non-)vegetarian")] = None,
    max_price: Annotated[int | None, Query(gt=0, description="Price limit in ₺")] = None,
) -> list[PizzaRead]:
    return await pizza_service.list_pizzas(
        db, vegetarian=vegetarian, max_price=max_price, limit=page.limit, offset=page.offset
    )


@router.get("/{pizza_id}", summary="Get one pizza", responses=NOT_FOUND)
async def get_pizza(pizza_id: int, db: DbSession) -> PizzaRead:
    return await pizza_service.get_pizza(db, pizza_id)


@router.post(
    "",
    status_code=201,
    summary="Add a pizza to the menu",
    dependencies=[Depends(require_api_key)],
    responses=UNAUTHORIZED,
)
async def create_pizza(payload: PizzaCreate, db: DbSession) -> PizzaRead:
    return await pizza_service.create_pizza(db, payload)


@router.patch(
    "/{pizza_id}",
    summary="Change a pizza",
    dependencies=[Depends(require_api_key)],
    responses=UNAUTHORIZED | NOT_FOUND,
)
async def update_pizza(pizza_id: int, payload: PizzaUpdate, db: DbSession) -> PizzaRead:
    return await pizza_service.update_pizza(db, pizza_id, payload)


@router.delete(
    "/{pizza_id}",
    status_code=204,
    summary="Take a pizza off the menu",
    dependencies=[Depends(require_api_key)],
    responses=UNAUTHORIZED | NOT_FOUND | CONFLICT,
)
async def delete_pizza(pizza_id: int, db: DbSession) -> None:
    await pizza_service.delete_pizza(db, pizza_id)
