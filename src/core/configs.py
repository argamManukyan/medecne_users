from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__name__).parent.parent.parent

MB_TO_BYTES: int = 1_048_576
SUPPORTED_IMAGE_TYPES = ["jpg", "jpeg", "webp", "png"]


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", case_sensitive=True)
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    DB_HOST: str

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def db_test_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}_test"


class AuthSettings(BaseSettings):
    private_key_path: Path = BASE_DIR / "src" / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "src" / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    token_type: str = "Bearer"
    access_token_lifetime: int = 15  # in minutes
    refresh_token_lifetime: int = 1  # in minutes
    password_min_length: int = 6
    password_max_length: int = 12


class FileSettings(BaseSettings):
    users_file_direction: str = "users"


class Settings(BaseSettings):
    api_version: str = "/api/v1"
    file_path: Path = BASE_DIR / "src" / "static" / "media"
    max_upload_file_size: int = 5242880  # 5mb
    db: DBSettings = DBSettings()
    file: FileSettings = FileSettings()
    auth: AuthSettings = AuthSettings()


settings = Settings()
