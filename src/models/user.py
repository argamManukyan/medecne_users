import datetime
from typing import Annotated, Optional

from annotated_types import MinLen
from pydantic import EmailStr
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, validates

from src.core.database import BaseModel


class User(BaseModel):
    __tablename__ = "user"

    first_name: Mapped[Annotated[str, MinLen(3)]] = mapped_column(String(20))
    last_name: Mapped[Annotated[str, MinLen(3)]] = mapped_column(String(20))
    email: Mapped[Annotated[str, EmailStr]] = mapped_column(unique=True)
    password: Mapped[Optional[bytes]]
    otp_code: Mapped[Optional[str]]
    last_login: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(default=False, nullable=True)
    attempts_count: Mapped[int] = mapped_column(nullable=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @validates("attempts_count")
    def validate_attempts_count(self, key, value):
        if value and (value < 0 or value > 3):
            raise ValueError("Please make sure in your steps.")
        return value


class Token(BaseModel):
    __tablename__ = "token"

    refresh_token: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    expired: Mapped[bool] = mapped_column(default=False)
