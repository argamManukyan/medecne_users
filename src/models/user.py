import datetime
from typing import Annotated, Optional

from annotated_types import MinLen
from pydantic import EmailStr
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from src.core.database import BaseModel


class UserGroup(BaseModel):
    __tablename__ = "usergroup"

    title: Mapped[str] = mapped_column(String(40), unique=True)
    users: Mapped[list["User"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    permissions: Mapped["Permission"] = relationship(
        "Permission", back_populates="group"
    )


class Permission(BaseModel):
    __tablename__ = "permission"

    group: Mapped["UserGroup"] = relationship("UserGroup", back_populates="permissions")
    user_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("usergroup.id"))
    policies: Mapped[JSON] = mapped_column(JSONB)


class UserRelatedFeatureValue(BaseModel):
    __tablename__ = "userrelatedfeaturevalue"

    value: Mapped[str] = mapped_column(String(200))
    feature: Mapped["UserRelatedFeatures"] = relationship(
        "UserRelatedFeatures", back_populates="values"
    )
    feature_id: Mapped[int] = mapped_column(ForeignKey("user_features.id"))
    UniqueConstraint("value", "feature_id", name="uix_1")


class UserRelatedFeatures(BaseModel):
    __tablename__ = "user_features"

    title: Mapped[str] = mapped_column(String(30))
    values: Mapped[Optional[list["UserRelatedFeatureValue"]]] = relationship(
        back_populates="feature", cascade="all, delete-orphan"
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    user: Mapped["User"] = relationship(
        "User", back_populates="features", cascade="all, delete"
    )


class User(BaseModel):
    __tablename__ = "user"

    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("usergroup.id"))
    group: Mapped["UserGroup"] = relationship(
        "UserGroup", back_populates="users", cascade="all, delete"
    )
    features: Mapped[Optional[list["UserRelatedFeatures"]]] = relationship(
        "UserRelatedFeatures",
        back_populates="user",
    )
    first_name: Mapped[Annotated[str, MinLen(3)]] = mapped_column(String(20))
    last_name: Mapped[Annotated[str, MinLen(3)]] = mapped_column(String(20))
    photo: Mapped[str] = mapped_column(nullable=True)
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
    def validate_attempts_count(self, _, value):
        if value and (value < 0 or value > 3):
            raise ValueError("Please make sure in your steps.")
        return value


class Token(BaseModel):
    __tablename__ = "token"

    refresh_token: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    expired: Mapped[bool] = mapped_column(default=False)
