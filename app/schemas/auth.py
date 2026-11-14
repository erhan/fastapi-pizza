from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr = Field(examples=["ayse@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["margherita-4ever"])
    full_name: str | None = Field(default=None, min_length=2, max_length=60, examples=["Ayşe"])

    @field_validator("email")
    @classmethod
    def lowercase(cls, value: str) -> str:
        return value.lower()


class UserRead(BaseModel):
    """What we say about a user. The password hash never leaves the kitchen."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
