from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


def pagination(limit: int = 10, offset: int = 0) -> dict[str, int]:
    return {"limit": limit, "offset": offset}


Pagination = Annotated[dict[str, int], Depends(pagination)]


def require_chef(x_api_key: Annotated[str | None, Header()] = None):
    if x_api_key != "chef-secret":
        raise HTTPException(401, "Only the chef can do that 👨‍🍳")


@app.get("/menu")
async def menu(page: Pagination):
    return {"page": page, "pizzas": ["Margherita", "Pepperoni"]}


@app.delete("/menu/{name}", dependencies=[Depends(require_chef)])
async def remove(name: str):
    return {"removed": name}
