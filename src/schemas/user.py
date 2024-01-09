import re
import datetime
from typing import Annotated, Optional

from annotated_types import MinLen, MaxLen
from pydantic import EmailStr, BaseModel, ConfigDict, field_validator, Field

from src import messages
from src.core.constants import PASSWORD_CHECKER_PATTERN


class UserRelatedFeaturesValueScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    value: str


class UserRelatedFeaturesScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    title: str
    values: list[UserRelatedFeaturesValueScheme] = Field(default_factory=list)


class UserBaseSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserCreateSchema(UserBaseSchema):
    group_id: int = 2
    password: Annotated[str, MinLen(6), MaxLen(12)]

    @field_validator("password")
    def val_password(cls, value: str):
        if not re.match(PASSWORD_CHECKER_PATTERN, value):
            raise ValueError(messages.PASSWORD_VALIDATION_PATTERN.format(length=6))
        return value


class UserUpdateSchema(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    features: list[UserRelatedFeaturesScheme] = Field(default_factory=list)


class UserResponseSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_login: Optional[datetime.datetime] = None
    is_active: bool
    group_id: int
    features: list[UserRelatedFeaturesScheme] = Field(default_factory=list)
    photo: str | bytes | None = None


class UserGroupScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    title: str
