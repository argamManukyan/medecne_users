from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.core.configs import BASE_DIR
from src.routers.user import user_router

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "src" / "static"), name="static")
app.include_router(user_router)
