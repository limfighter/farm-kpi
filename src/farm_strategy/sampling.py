"""Pure weather-pool selection and numerical sampling summaries."""
import math


def choose_pool(weather, window, *,
                invalid_window_message="window must be recent10 or all20"):
    """Select annual rows without reordering or mutating the observations."""
    if window not in ("recent10", "all20"):
        raise ValueError(invalid_window_message)
    pool = [row for row in weather if window == "all20" or row["year"] >= 2016]
    if len(pool) < 5:
        raise ValueError("Need >=5 annual observations")
    return pool


def quantile(v, q):
    """Linearly interpolate between sorted observations at fraction ``q``."""
    a = sorted(v)
    p = (len(a) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    return a[lo] if lo == hi else a[lo] * (hi - p) + a[hi] * (p - lo)
