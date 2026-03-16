import time
from math import floor


def time_in_ms() -> int:
    """
    Determines the current Unix timestamp measured in milliseconds.

    Returns:
        int: Unix timestamp in milliseconds.
    """
    return floor(time.time_ns() / 1e6)


def time_passed_since_ms(timestamp_in_ms: int) -> int:
    """
    Calcuates how much time has passed since a given Unix time measured in milliseconds.

    Args:
        timestamp_in_ms (int): The Unix millisecond timestamp to measure the difference from.

    Returns:
        int: The difference between the current Unix timestamp and the given timestamp measured in milliseconds.
    """
    return time_in_ms() - timestamp_in_ms
