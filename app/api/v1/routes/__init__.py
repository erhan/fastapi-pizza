from fastapi import APIRouter

from app.api.v1.routes import auth, health, orders, pizzas, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(pizzas.router, prefix="/pizzas", tags=["Pizzas"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
