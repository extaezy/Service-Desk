import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging():
    Path("logs").mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                "logs/bot.log",
                maxBytes=5_000_000,
                backupCount=3,
                encoding="utf-8"
            )
        ],
        force=True
    )