from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.exceptions import EmailTakenError, InvalidCredentialsError, NotAuthenticatedError
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserRead


async def register(db: AsyncSession, payload: UserCreate) -> UserRead:
    if await user_crud.get_user_by_email(db, payload.email) is not None:
        raise EmailTakenError()
    # Hashing takes a while on purpose. In a thread, the waiter keeps serving the other tables.
    hashed_password = await run_in_threadpool(security.hash_password, payload.password)
    try:
        user = await user_crud.create_user(
            db,
            {
                "email": payload.email,
                "full_name": payload.full_name,
                "hashed_password": hashed_password,
            },
        )
    except IntegrityError as exc:  # two sign-ups with the same e-mail at the same moment
        await db.rollback()
        raise EmailTakenError() from exc
    return UserRead.model_validate(user)


async def login(db: AsyncSession, *, email: str, password: str) -> Token:
    user = await user_crud.get_user_by_email(db, email.lower())
    if user is None or not user.is_active:
        raise InvalidCredentialsError()
    if not await run_in_threadpool(security.verify_password, password, user.hashed_password):
        raise InvalidCredentialsError()
    return Token(access_token=security.create_access_token(user.id))


async def get_user_from_token(db: AsyncSession, token: str) -> User:
    user_id = security.decode_access_token(token)
    user = await user_crud.get_user(db, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise NotAuthenticatedError()
    return user
