from enum import StrEnum

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class Topping(StrEnum):
    mozzarella = "mozzarella"
    pepperoni = "pepperoni"
    mushroom = "mushroom"
    basil = "basil"  # pineapple? not on this menu!


class PizzaCreate(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    price: int = Field(gt=0)
    toppings: list[Topping] = Field(min_length=1)


@app.post("/pizzas", status_code=201, response_model=PizzaCreate)
async def create_pizza(pizza: PizzaCreate):
    return pizza
