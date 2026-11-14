from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseTable


class User(BaseTable):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(60))
    hashed_password: Mapped[str] = mapped_column(String(255))  # never the password itself
    is_active: Mapped[bool] = mapped_column(default=True)
