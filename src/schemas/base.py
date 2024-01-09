from typing import Any
from pydantic import BaseModel


class BaseMessageResponse(BaseModel):
    """Uses when will be needed return messaging response"""

    message: str


class GenericSchema(BaseModel):
    data: dict | list

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        data = super().model_dump(*args, **kwargs)
        return data["data"]
