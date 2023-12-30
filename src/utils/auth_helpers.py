import uuid
from typing import Optional

import jwt
import datetime
import time

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from bcrypt import gensalt, hashpw, checkpw
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import constants
from src.core.configs import settings
from src.core.constants import TokenTypes, TOKEN_PARTITIONS_NUMBER, OTP_GENERATION_DIVISION
from src.core.database import get_session
from src.exceptions.auth_exceptions import InvalidData, UnAuthorized, TokenExpired
from src.schemas.auth import TokenResponseScheme
from src.models import Token

auth_scheme = HTTPBearer()


def encode_jwt(
    payload: dict,
    key: str = settings.auth.private_key_path.read_text(),
    algorithm: str = settings.auth.algorithm,
    expiration_delta: datetime.timedelta = datetime.timedelta(
        minutes=settings.auth.access_token_lifetime
    ),
):
    """Returns encoded JWT token"""

    payload["exp"] = datetime.datetime.now() + expiration_delta
    payload["iat"] = time.time()

    return jwt.encode(payload, key, algorithm)


def decode_jwt(
    token: str | bytes,
    key: str = settings.auth.public_key_path.read_text(),
    algorithm: str = settings.auth.algorithm,
):
    """Returns decoded JWT token"""

    decoded_data = jwt.decode(token, key, [algorithm])

    if decoded_data["exp"] < datetime.datetime.now().timestamp():
        raise TokenExpired

    return decoded_data


def hash_password(password: str) -> bytes:
    """Returns hashed password."""
    return hashpw(password.encode(), gensalt())


def validate_password(password: str, hashed_password: bytes) -> bool:
    """Validates and returns whether the user has typed correct password."""

    return checkpw(password.encode(), hashed_password)


def token_data(user_id: int, token_type: constants.TokenTypes):
    """Returns token data"""

    return {"sub": encode_user_id(user_id), "token_type": token_type.value}


def encode_user_id(user_id: int) -> str:
    """Encodes particular user.id"""
    return f"UI_{user_id}_{int(time.time())}"


def decode_user_id(user_decoded_id: str) -> int:
    """Decodes particular user.id"""
    separated_data = user_decoded_id.split("_")

    if not len(separated_data) == TOKEN_PARTITIONS_NUMBER:
        raise InvalidData

    user_id = int(separated_data[1])
    return user_id


async def check_token_validity(session: AsyncSession, **kwargs) -> Optional[Token]:
    """Returns is the token expired or no"""

    stmt = select(Token).filter_by(**kwargs)

    result = await session.scalars(stmt)

    if not (response := result.one_or_none()):
        raise UnAuthorized
    return response


async def validate_authenticated_user_token(
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    session: AsyncSession = Depends(get_session),
) -> int:
    """Validates and returns is the token valid"""
    try:
        await check_token_validity(
            session=session, access_token=token.credentials, expired=False
        )

        data = decode_jwt(token.credentials)

        if data["token_type"] != TokenTypes.ACCESS.value:
            raise InvalidData

        user_id = decode_user_id(data["sub"])

        return user_id

    except jwt.exceptions.InvalidTokenError:
        raise UnAuthorized


def generate_otp_code() -> str:
    """Generated OTP code for any purpose"""
    return f"{uuid.uuid4().int % OTP_GENERATION_DIVISION}"


def create_refresh_and_access_tokens(user_id: int) -> TokenResponseScheme:
    access_token: str = encode_jwt(
        payload=token_data(user_id=user_id, token_type=constants.TokenTypes.ACCESS)
    )
    refresh_token: str = encode_jwt(
        payload=token_data(user_id=user_id, token_type=constants.TokenTypes.REFRESH),
        expiration_delta=datetime.timedelta(days=settings.auth.refresh_token_lifetime),
    )
    return TokenResponseScheme(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=settings.auth.token_type,
    )
