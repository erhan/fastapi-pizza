from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseTable


class Order(BaseTable):
    __tablename__ = "orders"

    pizza_id: Mapped[int] = mapped_column(ForeignKey("pizzas.id"), index=True)
    pizza_name: Mapped[str] = mapped_column(String(40))  # snapshot: the menu may change later
    customer_name: Mapped[str] = mapped_column(String(60))
    quantity: Mapped[int]
    note: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(12))
    total_price: Mapped[int]
