def clamp(value: float, lower_bound: float, upper_bound: float) -> float:
    if value > upper_bound:
        return upper_bound
    if value < lower_bound:
        return lower_bound
    return value
