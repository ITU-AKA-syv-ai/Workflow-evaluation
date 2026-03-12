
import time
from math import floor


def time_in_ms() -> int:
    return floor(time.time_ns() / 1e6)


def time_passed_since_ms(timestamp_in_ms: int) -> int:
    return time_in_ms() - timestamp_in_ms
