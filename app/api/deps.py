import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.exceptions import UnauthorizedError

DbSession = Annotated[AsyncSession, Depends(get_db)]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, description="The chef's key")


async def require_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> None:
    """Only the chef (the API key holder) may change the menu or move orders along."""
    if api_key is None or not secrets.compare_digest(api_key.encode(), settings.api_key.encode()):
        raise UnauthorizedError()


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
