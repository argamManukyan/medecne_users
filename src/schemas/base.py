from pydantic import BaseModel


class BaseMessageResponse(BaseModel):
    """Uses when will be needed return messaging response"""

    message: str


