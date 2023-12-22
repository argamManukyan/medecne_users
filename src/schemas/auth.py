import re
from typing import Annotated

from annotated_types import MinLen, MaxLen
from pydantic import BaseModel, EmailStr, field_validator

from src import messages
from src.core.constants import PASSWORD_CHECKER_PATTERN


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class AccountVerificationScheme(BaseModel):
    email: str
    otp_code: str


class TokenResponseScheme(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenScheme(BaseModel):
    refresh_token: str


class PasswordResetScheme(BaseModel):
    email: str


class BasePasswordConfirmationScheme(BaseModel):
    new_password: Annotated[str, MinLen(6), MaxLen(12)]
    re_new_password: Annotated[str, MinLen(6), MaxLen(12)]

    @field_validator("new_password", "re_new_password")
    def val_password(cls, value: str):
        if not re.match(PASSWORD_CHECKER_PATTERN, value):
            raise ValueError(messages.PASSWORD_VALIDATION_PATTERN.format(length=6))
        return value


class ResetPasswordConfirmScheme(
    AccountVerificationScheme, BasePasswordConfirmationScheme
):
    ...


class SetNewPasswordScheme(BasePasswordConfirmationScheme):
    old_password: str
