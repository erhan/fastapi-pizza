from typing import Annotated

from fastapi import FastAPI, Header
from pydantic import BaseModel

app = FastAPI()


class Order(BaseModel):
    customer: str
    quantity: int = 1


@app.post("/pizzas/{pizza_id}/orders")
async def order_pizza(
    pizza_id: int,  # path
    order: Order,  # body
    extra_cheese: bool = False,  # query
    x_table_no: Annotated[int | None, Header()] = None,  # header
) -> dict[str, object]:
    return {
        "pizza_id": pizza_id,
        "extra_cheese": extra_cheese,
        "table": x_table_no,
        "order": order,
    }
