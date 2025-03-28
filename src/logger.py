import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


def setup_logging(logs_dir: str = "logs"):
    """
    Set up logging configuration for the bot.
    Logs are written to a file with date in filename and rotated daily.
    Args:
        logs_dir: Directory where log files are written.
    """
    os.makedirs(logs_dir, exist_ok=True)
    current_date = datetime.today().strftime("%d_%m_%Y")
    log_file = f"{logs_dir}/bot_{current_date}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # File handler - logs to a file
        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=14, encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        logger.addHandler(file_handler)

        # Console handler - logs to the terminal
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console_handler)

    logging.info("✅ Logging setup complete.")
