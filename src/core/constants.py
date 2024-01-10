from enum import Enum
from typing import NewType, Any


# Project constants

DbBaseModel = NewType("T", Any)
JsonType = NewType("T", str)
MAIN_OPERATIONS = ["create", "read", "update", "delete"]
ALLOW_ACTION = "ALLOW"
DENY_ACTION = "DENY"

# Auth constants

PASSWORD_CHECKER_PATTERN = "^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{6,}$"
TOKEN_PARTITIONS_NUMBER = 3
OTP_GENERATION_DIVISION = 100_0000


class TokenTypes(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
