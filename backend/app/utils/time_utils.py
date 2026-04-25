import time
from math import floor
from datetime import datetime, date


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


def datetime_from_json_string(json_timestamp: str) -> date | None:
    """
    Parses a date object from a JSON date formatted string

    Args:
       json_timestamp (str): A JSON date formatted string.

    Returns:
        date | None: The date if the string is correctly formatted, otherwise None.
    """
    try:
        return datetime.strptime(json_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return None
