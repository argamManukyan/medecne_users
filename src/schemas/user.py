import re
import datetime
from typing import Annotated, Optional

from annotated_types import MinLen, MaxLen
from pydantic import EmailStr, BaseModel, ConfigDict, field_validator

from src import messages
from src.core.constants import PASSWORD_CHECKER_PATTERN


class UserBaseSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserCreateSchema(UserBaseSchema):
    password: Annotated[str, MinLen(6), MaxLen(12)]

    @field_validator("password")
    def val_password(cls, value: str):
        if not re.match(PASSWORD_CHECKER_PATTERN, value):
            raise ValueError(messages.PASSWORD_VALIDATION_PATTERN.format(length=6))
        return value


class UserResponseSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_login: Optional[datetime.datetime] = None
    is_active: bool
