from fastapi import APIRouter

from app.api.v1.routes import health, orders, pizzas

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(pizzas.router, prefix="/pizzas", tags=["Pizzas"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
