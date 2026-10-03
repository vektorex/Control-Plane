"""
Exponential backoff with bounded decorrelated jitter calculation.
"""
import random
from typing import Optional


def compute_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    factor: float = 2.0,
    jitter: bool = True,
) -> float:
    """
    Computes exponential backoff delay with bounded jitter.
    formula: min(max_delay, base_delay * (factor ** (attempt - 1))) + uniform_jitter
    """
    if attempt <= 1:
        calculated = base_delay
    else:
        calculated = min(max_delay, base_delay * (factor ** (attempt - 1)))

    if jitter:
        # Full jitter between 0.5 * calculated and 1.5 * calculated, capped at max_delay
        half = calculated * 0.5
        calculated = random.uniform(half, calculated)

    return min(max_delay, max(0.1, calculated))
