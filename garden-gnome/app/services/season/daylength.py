"""Day length from latitude and date (NOAA solar equations). No data call.

Used for fall hardening (PLAN.md section 7: "day length under 13.5 hours").
Day length is sunrise to sunset with the standard 0.833 degree allowance for
refraction and the sun's disc, so it is a few minutes longer than the
geometric half day."""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional


def day_length_hours(lat: float, d: date) -> float:
    n = d.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (n - 1)
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma))
    phi = math.radians(lat)
    cos_h = ((math.cos(math.radians(90.833)) - math.sin(phi) * math.sin(decl))
             / (math.cos(phi) * math.cos(decl)))
    if cos_h <= -1:
        return 24.0
    if cos_h >= 1:
        return 0.0
    return 2 * math.degrees(math.acos(cos_h)) / 15.0


def first_day_shorter_than(lat: float, hours: float, year: int) -> Optional[date]:
    """The first day after the June solstice with day length under `hours`,
    or None when the days never get that long or never that short."""
    d = date(year, 6, 21)
    if day_length_hours(lat, d) < hours:
        return None  # the longest day is already shorter
    end = date(year, 12, 21)
    while d <= end:
        if day_length_hours(lat, d) < hours:
            return d
        d += timedelta(days=1)
    return None
