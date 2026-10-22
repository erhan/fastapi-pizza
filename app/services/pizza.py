from collections.abc import Iterable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PizzaInUseError, PizzaNotFoundError
from app.crud import order as order_crud
from app.crud import pizza as pizza_crud
from app.models.pizza import Pizza
from app.schemas.enums import MEAT_TOPPINGS
from app.schemas.pizza import PizzaCreate, PizzaRead, PizzaUpdate

# A Turkish-flavoured starter menu, inserted when the table is empty.
MENU: list[dict[str, Any]] = [
    {"name": "Margherita", "price": 190, "toppings": ["mozzarella", "tomato", "basil"]},
    {"name": "Pepperoni", "price": 230, "toppings": ["mozzarella", "tomato", "pepperoni"]},
    {"name": "Sucuklu", "price": 240, "toppings": ["mozzarella", "sucuk", "pepper"]},
    {
        "name": "Dört Peynirli",
        "price": 250,
        "size": "large",
        "toppings": ["mozzarella", "olive", "basil"],
    },
    {
        "name": "Vejetaryen",
        "price": 220,
        "toppings": ["mozzarella", "tomato", "mushroom", "olive", "pepper"],
    },
    {
        "name": "Karışık",
        "price": 260,
        "size": "large",
        "toppings": ["mozzarella", "tomato", "pepperoni", "sucuk", "mushroom", "olive", "pepper"],
    },
]


def _is_vegetarian(toppings: Iterable[str]) -> bool:
    return MEAT_TOPPINGS.isdisjoint(toppings)


async def _get_or_404(db: AsyncSession, pizza_id: int) -> Pizza:
    pizza = await pizza_crud.get_pizza(db, pizza_id)
    if pizza is None:
        raise PizzaNotFoundError()
    return pizza


async def list_pizzas(
    db: AsyncSession,
    *,
    vegetarian: bool | None,
    max_price: int | None,
    limit: int,
    offset: int,
) -> list[PizzaRead]:
    pizzas = await pizza_crud.list_pizzas(
        db, vegetarian=vegetarian, max_price=max_price, limit=limit, offset=offset
    )
    return [PizzaRead.model_validate(pizza) for pizza in pizzas]


async def get_pizza(db: AsyncSession, pizza_id: int) -> PizzaRead:
    return PizzaRead.model_validate(await _get_or_404(db, pizza_id))


async def create_pizza(db: AsyncSession, payload: PizzaCreate) -> PizzaRead:
    data = payload.model_dump(mode="json")
    data["is_vegetarian"] = _is_vegetarian(data["toppings"])
    return PizzaRead.model_validate(await pizza_crud.create_pizza(db, data))


async def update_pizza(db: AsyncSession, pizza_id: int, payload: PizzaUpdate) -> PizzaRead:
    pizza = await _get_or_404(db, pizza_id)
    # exclude_unset: only what the client sent. exclude_none: an explicit null changes nothing.
    data = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    if "toppings" in data:
        data["is_vegetarian"] = _is_vegetarian(data["toppings"])
    return PizzaRead.model_validate(await pizza_crud.update_pizza(db, pizza, data))


async def delete_pizza(db: AsyncSession, pizza_id: int) -> None:
    pizza = await _get_or_404(db, pizza_id)
    if await order_crud.has_orders_for_pizza(db, pizza_id):
        raise PizzaInUseError()
    await pizza_crud.delete_pizza(db, pizza)


async def seed_menu(db: AsyncSession) -> None:
    if await pizza_crud.count_pizzas(db) == 0:
        for item in MENU:
            await create_pizza(db, PizzaCreate.model_validate(item))
