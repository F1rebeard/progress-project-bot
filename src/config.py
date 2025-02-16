import logging

from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.logger import setup_logging


setup_logging()
logger = logging.getLogger(__name__)
load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    BOT_TOKEN: str
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **kwargs):
        super().__init__()
        logger.info("✅ Settings initialized successfully")
        logger.debug(f"🔹 DATABASE_URL: {self.DATABASE_URL}")
        logger.debug(f"🔹 BOT_TOKEN: {'*****' if self.BOT_TOKEN else 'Not Set'}")
        logger.debug(f"🔹 DEBUG: {self.DEBUG}")


settings = Settings()
