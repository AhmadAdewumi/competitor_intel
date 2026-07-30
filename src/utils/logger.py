# src/utils/logger.py

import sys
from pathlib import Path

from loguru import logger

# centralized logging for the app


def setup_logger(log_level: str = "INFO", log_file: str = "logs/competitor_intel.log"):
    """
    Configure the logger for the application using loguru

    :param log_level: minimum log_level to show(DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param log_file: Path to the log file
    :return: configured logger instance
    """

    # remove the default logger instance, coz we wanna tweak it o our taste
    logger.remove()

    logger.add(
        sys.stdout,  # send to standard output
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,  # only show log at or abpve this level
        backtrace=True,
        diagnose=True,
    )

    # For persistence
    # create path/dir
    log_dir = Path(log_file).parent
    if not log_dir.exists():
        log_dir.mkdir(
            parents=True, exist_ok=True
        )  # create parent dir and don't throw error if it exists

    # add file rotation
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=True,
    )

    # log that logger works
    logger.info(f"Logger configured with level: {log_level}")
    logger.info(f"log file created with name: {log_file}")

    return logger

    # creating a default logger instance


log = setup_logger()

## Example or su=imulation
if __name__ == "__main__":
    """
    demonstrates how to use the logger

    Run: python -m src.utils.logger
    """
    log.debug("This is a debug message (only shown with DEBUG level)")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")

    try:
        x = 1 / 0
    except ZeroDivisionError:
        log.exception("An error occured")
