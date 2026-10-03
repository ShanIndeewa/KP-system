"""
Geocoding and Time Zone Service

- Fetches coordinates for a place name from the OpenStreetMap Nominatim API.
- Finds the IANA time zone for coordinates (timezonefinder) and computes the
  historically correct UTC offset for a given local date/time (zoneinfo),
  so DST and past offset changes (e.g. Sri Lanka +6:30 in 1996) are handled.
"""

from datetime import datetime
from functools import lru_cache
from typing import Optional
from zoneinfo import ZoneInfo

import httpx
from timezonefinder import TimezoneFinder

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim usage policy requires an identifying User-Agent
USER_AGENT = "KP-Astrology-API/1.0"


@lru_cache(maxsize=1)
def _finder() -> TimezoneFinder:
    return TimezoneFinder()


async def geocode_place(query: str) -> dict:
    """
    Look up a place name via the Nominatim API.

    Returns dict with name, latitude, longitude.
    Raises ValueError if not found, RuntimeError if the service is unreachable.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.get(
                NOMINATIM_URL,
                params={"q": query, "format": "jsonv2", "limit": 1},
            )
            resp.raise_for_status()
            results = resp.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Geocoding service error: {e}")

    if not results:
        raise ValueError(f"Place '{query}' not found")

    top = results[0]
    return {
        "name": top.get("display_name", query),
        "latitude": float(top["lat"]),
        "longitude": float(top["lon"]),
    }


def get_timezone_name(latitude: float, longitude: float) -> Optional[str]:
    """Return IANA time zone name (e.g. 'Asia/Colombo') for coordinates."""
    return _finder().timezone_at(lat=latitude, lng=longitude)


def get_utc_offset(latitude: float, longitude: float, local_dt: datetime) -> tuple:
    """
    Get the UTC offset (hours) in effect at the given local date/time.

    Returns (offset_hours, tz_name). Raises ValueError if no zone is found.
    """
    tz_name = get_timezone_name(latitude, longitude)
    if not tz_name:
        raise ValueError("Could not determine time zone for these coordinates")
    offset = local_dt.replace(tzinfo=ZoneInfo(tz_name)).utcoffset()
    return offset.total_seconds() / 3600.0, tz_name
