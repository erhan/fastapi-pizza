from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, PageParams
from app.schemas.auth import UserRead
from app.schemas.common import NOT_AUTHENTICATED
from app.schemas.order import OrderRead
from app.services import order as order_service

router = APIRouter()


@router.get("/me", summary="Who am I?", responses=NOT_AUTHENTICATED)
async def get_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.get("/me/orders", summary="My orders", responses=NOT_AUTHENTICATED)
async def list_my_orders(user: CurrentUser, db: DbSession, page: PageParams) -> list[OrderRead]:
    return await order_service.list_orders(
        db, limit=page.limit, offset=page.offset, user_id=user.id
    )
