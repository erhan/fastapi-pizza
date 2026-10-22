from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.enums import OrderStatus

MESSAGES = {
    OrderStatus.preparing: "Thanks {name}! {qty} × {pizza} is being prepared 👨‍🍳",
    OrderStatus.baking: "Hold tight, {name}: {qty} × {pizza} is in the oven 🔥",
    OrderStatus.on_the_way: "{qty} × {pizza} is on the way 🛵 Get the plates ready!",
    OrderStatus.delivered: "Delivered! Afiyet olsun, {name} 🍕",
}


class OrderCreate(BaseModel):
    pizza_id: int = Field(gt=0, examples=[1])
    customer_name: str = Field(min_length=2, max_length=60, examples=["Ayşe"])
    quantity: int = Field(default=1, ge=1, le=10)
    note: str | None = Field(default=None, max_length=200, examples=["Extra basil, please"])


class OrderUpdate(BaseModel):
    status: OrderStatus


class OrderRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "pizza_id": 1,
                    "pizza_name": "Margherita",
                    "customer_name": "Ayşe",
                    "quantity": 2,
                    "note": "Extra basil, please",
                    "status": "preparing",
                    "total_price": 380,
                    "created_at": "2026-11-14T12:00:00",
                    "message": "Thanks Ayşe! 2 × Margherita is being prepared 👨‍🍳",
                }
            ]
        },
    )

    id: int
    pizza_id: int
    pizza_name: str
    customer_name: str
    quantity: int
    note: str | None
    status: OrderStatus
    total_price: int = Field(description="Price in ₺")
    created_at: datetime

    @computed_field
    @property
    def message(self) -> str:
        return MESSAGES[self.status].format(
            name=self.customer_name, qty=self.quantity, pizza=self.pizza_name
        )
