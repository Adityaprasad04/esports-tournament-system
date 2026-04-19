"""utils/logger.py — Structured logging for NexusArena backend"""
import logging
import sys

def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("nexusarena")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)
    return logger

logger = _setup_logger()
