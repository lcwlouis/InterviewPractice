import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar('T')


def call_with_retry(func: Callable[[], T], retries: int = 3, delay_seconds: float = 0.2) -> T:
    if retries <= 0:
        raise ValueError('retries must be greater than 0')

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return func()
        except Exception as err:  # noqa: BLE001
            last_error = err
            if attempt < retries - 1:
                time.sleep(delay_seconds)
    if last_error:
        raise last_error
    raise RuntimeError('call_with_retry failed unexpectedly')
