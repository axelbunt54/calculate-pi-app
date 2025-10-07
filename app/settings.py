import os

from loguru import logger
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))


class Settings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @computed_field
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    LOG_FORMAT: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, "..", ".env"), extra="ignore"
    )


settings = Settings()

log_file_path = os.path.join(BASE_DIR, "..", "log.txt")
logger.add(
    log_file_path,
    format=settings.LOG_FORMAT,
    level="INFO",
    rotation=settings.LOG_ROTATION,
)
