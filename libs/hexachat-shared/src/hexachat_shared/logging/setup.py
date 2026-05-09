"""Loguru bootstrap reused by every service.

The reference project pulls a flat list of named loggers; here each service
binds itself once with ``service=...`` and gets a JSON sink in non-local
environments and a coloured human sink in local development.
"""

from __future__ import annotations

import sys
from typing import Final

from loguru import logger

_DEV_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
    "<level>{level: <8}</level> "
    "<cyan>{extra[service]}</cyan> "
    "<level>{message}</level>"
)


def configure_logging(*, service: str, level: str = "INFO", json: bool = False) -> None:
    """Replace loguru's default handler with one tailored to the service.

    Idempotent — safe to call multiple times (e.g. from tests).
    """
    logger.remove()
    if json:
        logger.add(sys.stdout, level=level, serialize=True, backtrace=False, diagnose=False)
    else:
        logger.add(sys.stdout, level=level, format=_DEV_FORMAT, backtrace=True, diagnose=False)
    logger.configure(extra={"service": service})
