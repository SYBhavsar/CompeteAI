"""
Retry utilities for API calls
Implements exponential backoff for resilient API calls
"""
import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: Optional[int] = None,
    initial_delay: Optional[float] = None,
    backoff_multiplier: Optional[float] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts (defaults to settings)
        initial_delay: Initial delay in seconds (defaults to settings)
        backoff_multiplier: Exponential backoff multiplier (defaults to settings)
        exceptions: Tuple of exceptions to catch and retry

    Usage:
        @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
        def call_openai_api():
            ...
    """
    max_retries = max_retries or settings.max_retries
    initial_delay = initial_delay or settings.retry_delay
    backoff_multiplier = backoff_multiplier or settings.retry_backoff

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"All {max_retries} retry attempts failed for {func.__name__}: {str(e)}"
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


def retry_async_with_backoff(
    max_retries: Optional[int] = None,
    initial_delay: Optional[float] = None,
    backoff_multiplier: Optional[float] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Async version of retry_with_backoff decorator

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_multiplier: Exponential backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
    """
    import asyncio

    max_retries = max_retries or settings.max_retries
    initial_delay = initial_delay or settings.retry_delay
    backoff_multiplier = backoff_multiplier or settings.retry_backoff

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"All {max_retries} retry attempts failed for {func.__name__}: {str(e)}"
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator
