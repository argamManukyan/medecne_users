from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.core.configs import settings, BASE_DIR
from src.routers.user import user_router

app = FastAPI()
app.router.prefix = settings.api_version
app.mount("/static", StaticFiles(directory=BASE_DIR / "src" / "static"), name="static")
app.include_router(user_router)
