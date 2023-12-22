from src import messages
from fastapi import HTTPException, status


UserDoesNotFound = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail=messages.USER_DOES_NOT_EXISTS
)


EmailDuplication = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail=messages.EMAIL_DUPLICATION
)


UnAuthorized = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_CREDENTIALS
)


AccountAlreadyVerified = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail=messages.ACCOUNT_VERIFIED_ISSUE
)


PermissionDenied = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail=messages.PERMISSION_DENIED
)


PasswordsDidNotMatch = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail=messages.PASSWORDS_DID_NOT_MATCH
)

UnActivated = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.UN_ACTIVE_ACCOUNT
)


AccountDeleted = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.ACCOUNT_DELETED
)


TokenExpired = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.TOKEN_IS_EXPIRED
)


# class based exceptions


class InvalidData(HTTPException):
    def __init__(self, message: str = None):
        if message:
            message = f"{messages.INVALID_DATA}: {message}"
        else:
            message = messages.INVALID_DATA

        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


class InvalidOTP(HTTPException):
    def __init__(self, attempts_num):
        message = messages.INVALID_OTP_CODE.format(number=attempts_num)
        super().__init__(status.HTTP_403_FORBIDDEN, message)
