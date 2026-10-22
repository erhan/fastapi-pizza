from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseTable


class Pizza(BaseTable):
    __tablename__ = "pizzas"

    name: Mapped[str] = mapped_column(String(40))
    price: Mapped[int]  # whole ₺ to keep the demo simple; real money deserves Decimal
    size: Mapped[str] = mapped_column(String(10))
    toppings: Mapped[list[str]] = mapped_column(JSON)
    is_vegetarian: Mapped[bool] = mapped_column(index=True)
