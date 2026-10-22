from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import Size, Topping


class PizzaCreate(BaseModel):
    name: str = Field(min_length=2, max_length=40, examples=["Margherita"])
    price: int = Field(gt=0, le=2000, description="Price in ₺", examples=[190])
    size: Size = Size.medium
    toppings: list[Topping] = Field(
        min_length=1, max_length=8, examples=[["mozzarella", "tomato", "basil"]]
    )


class PizzaUpdate(BaseModel):
    """Every field is optional: send only what changes."""

    name: str | None = Field(default=None, min_length=2, max_length=40)
    price: int | None = Field(default=None, gt=0, le=2000)
    size: Size | None = None
    toppings: list[Topping] | None = Field(default=None, min_length=1, max_length=8)


class PizzaRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Margherita",
                    "price": 190,
                    "size": "medium",
                    "toppings": ["mozzarella", "tomato", "basil"],
                    "is_vegetarian": True,
                    "created_at": "2026-11-14T12:00:00",
                }
            ]
        },
    )

    id: int
    name: str
    price: int = Field(description="Price in ₺")
    size: Size
    toppings: list[Topping]
    is_vegetarian: bool
    created_at: datetime
