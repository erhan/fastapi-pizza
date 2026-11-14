from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.exceptions import EmailTakenError, InvalidCredentialsError, NotAuthenticatedError
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserRead


async def register(db: AsyncSession, payload: UserCreate) -> UserRead:
    # Hashing takes a while on purpose. In a thread, the waiter keeps serving the other tables.
    # And it comes first: once a session has run a query it holds on to its database connection,
    # and nobody should have to wait for a connection while we are busy hashing.
    hashed_password = await security.run_in_hasher(security.hash_password, payload.password)
    if await user_crud.get_user_by_email(db, payload.email) is not None:
        raise EmailTakenError()
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
    await db.close()  # hand the connection back before the slow part: checking the password
    if user is None or not user.is_active:
        raise InvalidCredentialsError()
    if not await security.run_in_hasher(security.verify_password, password, user.hashed_password):
        raise InvalidCredentialsError()
    return Token(access_token=security.create_access_token(user.id))


async def get_user_from_token(db: AsyncSession, token: str) -> User:
    user_id = security.decode_access_token(token)
    user = await user_crud.get_user(db, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise NotAuthenticatedError()
    return user
