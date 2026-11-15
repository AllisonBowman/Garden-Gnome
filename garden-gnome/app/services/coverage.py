"""Which pins count as United States places: one rule for the whole app.

The site profile asks the United States geodata services only about these
pins, and the new routes never send them to Open-Meteo (build spec
section 2, PLAN.md D11). The seasonal forecast and the site profile both use
this module, so the two halves of the app agree about the same pin.

The test is a set of rough boxes around the states and territories, minus
boxes around the foreign cities and coasts the rough boxes would otherwise
take in (southern Canada along the border, northern Mexico, the Bahamas).
It is deliberately rough near a border: the Weather Service's own lookup
(a 404 for a place it does not cover) settles the weather side, see
`app.services.season.forecast`.
"""
from __future__ import annotations

#: (south, north, west, east) in degrees.
US_BOXES: tuple[tuple[float, float, float, float], ...] = (
    (24.0, 49.6, -125.0, -66.5),    # contiguous states
    (51.0, 71.6, -180.0, -129.0),   # Alaska
    (18.8, 22.4, -160.6, -154.7),   # Hawaii
    (17.6, 18.6, -67.4, -64.5),     # Puerto Rico and the United States Virgin Islands
    (13.2, 15.4, 144.5, 146.2),     # Guam and the Northern Mariana Islands
    (-14.7, -11.0, -171.2, -168.1),  # American Samoa
)

#: Inside the boxes above but not the United States.
NOT_US_BOXES: tuple[tuple[float, float, float, float], ...] = (
    (49.0, 49.6, -125.0, -95.3),    # Canada north of the 49th parallel (Vancouver, Winnipeg)
    (48.42, 49.0, -125.0, -123.25),  # Victoria and southern Vancouver Island
    (43.3, 45.02, -81.7, -76.6),    # southern Ontario north of Lake Ontario (Toronto)
    (42.6, 43.3, -82.3, -79.15),    # southern Ontario west of Niagara (Hamilton, London)
    (45.02, 49.6, -82.5, -71.5),    # Ontario and Quebec north of New York and Vermont
    (46.5, 49.6, -71.5, -70.1),     # Quebec City
    (45.6, 49.6, -67.75, -66.5),    # New Brunswick
    (24.0, 31.28, -117.0, -106.5),  # Mexico south of Arizona and New Mexico
    (31.28, 32.52, -117.2, -114.8),  # Tijuana and northern Baja California
    (24.0, 28.9, -106.5, -100.9),   # Mexico south of the Big Bend
    (24.0, 27.4, -100.9, -99.4),    # Mexico south of Laredo (Monterrey)
    (24.0, 25.8, -99.4, -97.0),     # Mexico south of the lower Rio Grande
    (24.0, 27.3, -79.3, -72.0),     # the Bahamas
    (60.35, 71.6, -140.95, -129.0),  # Yukon and northern British Columbia
    (51.0, 54.6, -134.0, -129.0),   # Haida Gwaii and Prince Rupert
)


def _inside(boxes, lat: float, lng: float) -> bool:
    return any(s <= lat <= n and w <= lng <= e for s, n, w, e in boxes)


def in_united_states(lat: float, lng: float) -> bool:
    """True for a pin in the United States or its territories (roughly, as
    the module note says)."""
    return _inside(US_BOXES, lat, lng) and not _inside(NOT_US_BOXES, lat, lng)


def in_territory(lat: float, lng: float) -> bool:
    """True for Puerto Rico, the Virgin Islands, Guam, the Northern Mariana
    Islands and American Samoa (and Hawaii): islands with no foreign land
    in their boxes, so they are the United States however the Weather
    Service answers."""
    return in_united_states(lat, lng) and _inside(US_BOXES[3:], lat, lng)
