from typing import Annotated

from fastapi import APIRouter, Depends, status, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.oauth2 import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database import get_session
from src.core.configs import SUPPORTED_IMAGE_TYPES, settings
from src.schemas.base import BaseMessageResponse
from src.utils.auth_helpers import validate_authenticated_user_token, auth_scheme
from src.schemas.user import UserResponseSchema, UserCreateSchema, UserUpdateSchema
from src.schemas.auth import (
    LoginSchema,
    AccountVerificationScheme,
    TokenResponseScheme,
    ResetPasswordConfirmScheme,
    PasswordResetScheme,
    SetNewPasswordScheme,
    RefreshTokenScheme,
)
from src.services import user_service
from src.messages import PHOTO_UPDATED
from src.utils.base_helpers import validate_file, check_content_type

user_router = APIRouter(prefix=f"{settings.api_version}/auth", tags=["Auth"])

auth_backend = OAuth2PasswordBearer(tokenUrl=f"{settings.api_version}/auth/login")


@user_router.post(
    "/register", response_model=BaseMessageResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: UserCreateSchema, session: AsyncSession = Depends(get_session)
):
    data = await user_service.create_user(data=payload, session=session)
    return data


@user_router.post("/verify", response_model=BaseMessageResponse)
async def verify_account(
    payload: AccountVerificationScheme, session: AsyncSession = Depends(get_session)
):
    data = await user_service.verify_account(data=payload, session=session)
    return data


@user_router.post("/login", response_model=TokenResponseScheme)
async def login(payload: LoginSchema, session: AsyncSession = Depends(get_session)):
    return await user_service.login(login_data=payload, session=session)


@user_router.get("/profile", response_model=UserResponseSchema)
async def profile(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(validate_authenticated_user_token),
):
    user = await user_service.get_user(id=user_id, session=session)
    return UserResponseSchema.model_validate(user)


@user_router.patch("/profile", response_model=UserResponseSchema)
async def update_profile(
    payload: UserUpdateSchema,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(validate_authenticated_user_token),
):
    user = await user_service.patch_user(
        session=session, payload=payload, user_id=user_id
    )
    return UserResponseSchema.model_validate(user)


@user_router.patch("/profile-photo", response_model=BaseMessageResponse)
@check_content_type(SUPPORTED_IMAGE_TYPES)
async def profile_photo(
    file: UploadFile = Depends(validate_file),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(validate_authenticated_user_token),
):
    await user_service.update_profile_photo(session=session, user_id=user_id, file=file)

    return BaseMessageResponse(message=PHOTO_UPDATED)


@user_router.post("/resend-otp", response_model=BaseMessageResponse)
async def resend_otp(
    payload: LoginSchema, session: AsyncSession = Depends(get_session)
):
    return await user_service.request_otp(payload=payload, session=session)


@user_router.post("/reset-password")
async def reset_password(
    payload: PasswordResetScheme, session: AsyncSession = Depends(get_session)
):
    return await user_service.reset_password(email=payload.email, session=session)


@user_router.post("/reset-password-confirm")
async def reset_password_confirm(
    payload: ResetPasswordConfirmScheme, session: AsyncSession = Depends(get_session)
):
    return await user_service.reset_password_confirm(payload=payload, session=session)


@user_router.post("/set-new-password")
async def set_new_password(
    payload: SetNewPasswordScheme,
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: int = Depends(validate_authenticated_user_token),
):
    return await user_service.set_new_password(
        user_id=user_id, session=session, payload=payload
    )


@user_router.post("/refresh", response_model=TokenResponseScheme)
async def refresh_token(
    payload: RefreshTokenScheme,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await user_service.refresh_token(payload=payload, session=session)


@user_router.get("/logout", response_model=BaseMessageResponse)
async def logout(
    session: Annotated[AsyncSession, Depends(get_session)],
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    return await user_service.logout(token=token.credentials, session=session)
