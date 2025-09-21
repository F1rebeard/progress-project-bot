from loguru import logger


def setup_logging(logs_dir: str = "logs"):
    """
    Configure the Loguru logger.
    """
    logger.add(
        "logs/bot.log",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        level="DEBUG",
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        enqueue=True,
    )