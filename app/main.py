from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes import api_router
from app.core.config import settings
from app.core.db import SessionLocal, create_db_and_tables
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import ProcessTimeMiddleware
from app.services import pizza as pizza_service

DESCRIPTION = """
Order a pizza over HTTP 🍕 The companion API of the talk **A Slice of FastAPI**
(Python Pizza Istanbul 2026).

* **Browse the menu** and **order a pizza**: no key needed.
* **Changing the menu** (or moving an order along) is chef-only: press **Authorize** and
  send the chef's key in the `X-API-Key` header.
* Pineapple is not a topping here. Try it. 🍍
"""

TAGS_METADATA = [
    {"name": "Pizzas", "description": "The menu. Reading is free, changing it is chef-only."},
    {"name": "Orders", "description": "Order a pizza and follow it to your door."},
    {"name": "Health", "description": "Is the oven hot?"},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.create_tables_on_startup:
        await create_db_and_tables()
    if settings.seed_on_startup:
        async with SessionLocal() as db:
            await pizza_service.seed_menu(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        contact={"name": "Erhan BÜTE", "url": "https://erhan.dev"},
        license_info={"name": "MIT", "identifier": "MIT"},
        lifespan=lifespan,
    )

    app.add_middleware(ProcessTimeMiddleware)
    setup_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"message": "Welcome to the pizzeria! 🍕", "docs": "/docs"}

    return app


app = create_app()
