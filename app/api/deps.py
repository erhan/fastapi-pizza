import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.exceptions import NotAuthenticatedError, UnauthorizedError
from app.models.user import User
from app.services import auth as auth_service

DbSession = Annotated[AsyncSession, Depends(get_db)]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, description="The chef's key")


async def require_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> None:
    """Only the chef (the API key holder) may change the menu or move orders along."""
    if api_key is None or not secrets.compare_digest(api_key.encode(), settings.api_key.encode()):
        raise UnauthorizedError()


# Customers log in with e-mail + password and get a JWT; `/docs` does it via the Authorize button.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/token",
    auto_error=False,
    description="Log in as a customer: put your e-mail in the username field",
)


async def get_optional_user(
    db: DbSession, token: Annotated[str | None, Depends(oauth2_scheme)]
) -> User | None:
    """The logged-in customer, or None for a guest. A token that is sent must be valid."""
    if token is None:
        return None
    return await auth_service.get_user_from_token(db, token)


async def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise NotAuthenticatedError()
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@dataclass(frozen=True)
class Page:
    limit: int
    offset: int


def get_page(
    limit: Annotated[int, Query(ge=1, le=50, description="Page size")] = 10,
    offset: Annotated[int, Query(ge=0, description="How many rows to skip")] = 0,
) -> Page:
    return Page(limit=limit, offset=offset)


PageParams = Annotated[Page, Depends(get_page)]
