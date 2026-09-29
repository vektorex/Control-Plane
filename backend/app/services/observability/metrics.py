import math
from typing import List, Optional, Union


def calculate_percentile(values: List[Union[int, float]], percentile: float) -> Optional[float]:
    """
    Calculates the given percentile (0 to 100) from a list of numeric values.
    """
    if not values:
        return None

    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return round(float(sorted_vals[int(k)]), 2)

    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return round(float(d0 + d1), 2)


def calculate_average(values: List[Union[int, float]]) -> Optional[float]:
    """
    Calculates average of numeric values, rounded to 2 decimal places.
    """
    if not values:
        return None
    return round(sum(values) / len(values), 2)
