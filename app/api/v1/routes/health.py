from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthRead

router = APIRouter()


@router.get("/health", summary="Is the oven hot?")
async def health() -> HealthRead:
    return HealthRead(status="ok", app=settings.app_name, version=settings.version)
