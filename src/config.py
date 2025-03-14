import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.logger import setup_logging


setup_logging()
logger = logging.getLogger(__name__)
load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    DEBUG: bool = False
    ADMIN_IDS: list[int]
    BOT_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **kwargs):
        super().__init__()
        logger.info("✅ Settings initialized successfully")
        logger.debug(f"🔹 DATABASE_URL: {self.DATABASE_URL}")
        logger.debug(f"🔹 BOT_TOKEN: {'*****' if self.BOT_TOKEN else 'Not Set'}")
        logger.debug(f"🔹 DEBUG: {self.DEBUG}")


settings = Settings()
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML, protect_content=True),
)
dp = Dispatcher(storage=MemoryStorage())
admins = settings.ADMIN_IDS
database_url = str(settings.DATABASE_URL)
