from fastapi import FastAPI
from src.core.configs import settings
from src.routers.user import user_router

app = FastAPI()
app.router.prefix = settings.api_version

app.include_router(user_router)
