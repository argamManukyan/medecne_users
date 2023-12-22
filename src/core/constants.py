# Auth constants
from enum import Enum

PASSWORD_CHECKER_PATTERN = "^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{6,}$"


class TokenTypes(Enum):
    ACCESS = "access"
    REFRESH = "refresh"

