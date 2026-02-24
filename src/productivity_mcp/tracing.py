"""Observability via tracing decorator and stderr logging (Pattern 4)."""

import functools
import logging
import sys
import time


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("productivity_mcp")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


logger = setup_logging()


def traced(func):
    """Async decorator that logs entry, exit, timing, and errors for tool calls."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        name = func.__name__
        logger.info(f"-> {name} called with kwargs={kwargs}")
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"<- {name} completed in {elapsed:.1f}ms")
            return result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"<- {name} failed in {elapsed:.1f}ms: {exc}")
            raise

    return wrapper
