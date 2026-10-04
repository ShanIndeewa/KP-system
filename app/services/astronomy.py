"""
High-Precision Astronomical Calculations using Skyfield

Uses JPL DE421 ephemeris for accurate planetary positions.
This replaces the simplified VSOP87 approximations with NASA-level accuracy.
"""

import math
from typing import Tuple, Dict, List
from datetime import datetime, timezone
import os

# Skyfield imports
from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame


# Cache for ephemeris data
_ts = None
_eph = None
_planets_cache = {}


def _get_ephemeris():
    """Load and cache the JPL ephemeris data."""
    global _ts, _eph, _planets_cache
    
    if _ts is None:
        _ts = load.timescale()
    
    if _eph is None:
        # Download DE421 ephemeris (covers 1900-2050 with high accuracy)
        try:
            _eph = load('de421.bsp')
        except:
            # Fallback to DE440s if DE421 not available
            _eph = load('de440s.bsp')
        
        # Cache planet objects
        _planets_cache = {
            'Sun': _eph['sun'],
            'Moon': _eph['moon'],
            'Mercury': _eph['mercury barycenter'],
            'Venus': _eph['venus barycenter'],
            'Mars': _eph['mars barycenter'],
            'Jupiter': _eph['jupiter barycenter'],
            'Saturn': _eph['saturn barycenter'],
            'Earth': _eph['earth']
        }
    
    return _ts, _eph, _planets_cache


def date_to_julian_day(year: int, month: int, day: int,
                        hour: int = 0, minute: int = 0, second: float = 0.0,
                        timezone_offset: float = 0.0) -> float:
    """
    Convert date/time to Julian Day Number.
    
    Args:
        year: Year (e.g., 2002)
        month: Month (1-12)
        day: Day (1-31)
        hour: Hour in 24-hour format (0-23)
        minute: Minute (0-59)
        second: Second (0-59.999...)
        timezone_offset: Timezone offset from UTC
        
    Returns:
        Julian Day Number (UT)
    """
    # Convert local time to UT
    decimal_hour = hour + minute / 60.0 + second / 3600.0 - timezone_offset
    
    # Adjust date if UT goes to previous/next day
    day_fraction = decimal_hour / 24.0
    
    # Handle year/month adjustment for Jan/Feb
    if month <= 2:
        year -= 1
        month += 12
    
    # Calculate Julian Day using standard algorithm
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    jd += day_fraction
    
    return jd


def julian_day_to_date(jd: float) -> Tuple[int, int, int, float]:
    """Convert Julian Day to calendar date."""
    jd = jd + 0.5
    Z = int(jd)
    F = jd - Z
    
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)
    
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    
    day = B - D - int(30.6001 * E)
    
    if E < 14:
        month = E - 1
    else:
        month = E - 13
    
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
    
    decimal_hour = F * 24.0
    
    return year, month, day, decimal_hour


def normalize_angle(angle: float) -> float:
    """Normalize angle to 0-360 range."""
    while angle < 0:
        angle += 360.0
    while angle >= 360:
        angle -= 360.0
    return angle


def calculate_planet_longitude_skyfield(jd: float, planet_name: str) -> Tuple[float, float, bool]:
    """
    Calculate a planet's tropical ecliptic longitude using Skyfield.
    
    Args:
        jd: Julian Day Number
        planet_name: Name of planet
        
    Returns:
        Tuple of (longitude, latitude, is_retrograde)
    """
    ts, eph, planets = _get_ephemeris()
    
    # Convert JD to Skyfield time
    t = ts.tt_jd(jd)
    
    # Get Earth position
    earth = planets['Earth']
    
    if planet_name == 'Sun':
        sun = planets['Sun']
        astrometric = earth.at(t).observe(sun)
        apparent = astrometric.apparent()
        
        # Get ecliptic coordinates
        lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
        longitude = lon.degrees
        latitude = lat.degrees
        
        # Sun is never retrograde from Earth's perspective
        is_retrograde = False
        
    elif planet_name == 'Moon':
        moon = planets['Moon']
        astrometric = earth.at(t).observe(moon)
        apparent = astrometric.apparent()
        
        lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
        longitude = lon.degrees
        latitude = lat.degrees
        is_retrograde = False
        
    else:
        planet = planets.get(planet_name)
        if planet is None:
            return 0.0, 0.0, False
        
        astrometric = earth.at(t).observe(planet)
        apparent = astrometric.apparent()
        
        lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
        longitude = lon.degrees
        latitude = lat.degrees
        
        # Check retrograde by comparing current and previous position
        t_prev = ts.tt_jd(jd - 1)
        astrometric_prev = earth.at(t_prev).observe(planet)
        apparent_prev = astrometric_prev.apparent()
        lat_prev, lon_prev, _ = apparent_prev.frame_latlon(ecliptic_frame)
        
        # Calculate daily motion
        daily_motion = longitude - lon_prev.degrees
        if daily_motion > 180:
            daily_motion -= 360
        elif daily_motion < -180:
            daily_motion += 360
        
        is_retrograde = daily_motion < 0
    
    return normalize_angle(longitude), latitude, is_retrograde


def calculate_rahu_position(jd: float) -> float:
    """
    Calculate Mean Lunar Node (Rahu) position.
    
    The Moon's mean ascending node (Rahu) regresses through the zodiac.
    This uses the standard mean node formula for accuracy.
    """
    # Julian centuries from J2000.0
    T = (jd - 2451545.0) / 36525.0
    
    # Mean longitude of ascending node (Rahu)
    # Using high-precision formula from Meeus
    omega = 125.0445479
    omega -= 1934.1362891 * T
    omega += 0.0020754 * T * T
    omega += T * T * T / 467441.0
    omega -= T * T * T * T / 60616000.0
    
    return normalize_angle(omega)


def calculate_sun_position(jd: float) -> float:
    """Calculate Sun's tropical longitude."""
    lon, lat, retro = calculate_planet_longitude_skyfield(jd, 'Sun')
    return lon


def calculate_moon_position(jd: float) -> float:
    """Calculate Moon's tropical longitude."""
    lon, lat, retro = calculate_planet_longitude_skyfield(jd, 'Moon')
    return lon


def calculate_planet_position(jd: float, planet: str) -> Tuple[float, bool]:
    """
    Calculate a planet's tropical longitude.
    
    Args:
        jd: Julian Day
        planet: Planet name
        
    Returns:
        Tuple of (longitude, is_retrograde)
    """
    lon, lat, retro = calculate_planet_longitude_skyfield(jd, planet)
    return lon, retro


def calculate_obliquity(jd: float) -> float:
    """Calculate the obliquity of the ecliptic."""
    T = (jd - 2451545.0) / 36525.0
    eps = 23.439291 - 0.0130042 * T - 0.00000016 * T * T + 0.000000504 * T * T * T
    return eps


def calculate_sidereal_time(jd: float, longitude: float) -> float:
    """
    Calculate Local Sidereal Time.
    
    Args:
        jd: Julian Day
        longitude: Geographic longitude (East positive)
        
    Returns:
        Local Sidereal Time in degrees (0-360)
    """
    T = (jd - 2451545.0) / 36525.0
    
    # Greenwich Mean Sidereal Time at 0h UT
    theta0 = 280.46061837 + 360.98564736629 * (jd - 2451545.0)
    theta0 += 0.000387933 * T * T - T * T * T / 38710000.0
    
    # Add longitude to get Local Sidereal Time
    LST = normalize_angle(theta0 + longitude)
    
    return LST


def calculate_ascendant(jd: float, latitude: float, longitude: float) -> float:
    """
    Calculate the Ascendant (tropical longitude).
    
    Uses the standard formula from Meeus "Astronomical Algorithms".
    """
    LST = calculate_sidereal_time(jd, longitude)
    LST_rad = math.radians(LST)
    
    eps = calculate_obliquity(jd)
    eps_rad = math.radians(eps)
    
    lat_rad = math.radians(latitude)
    
    # Ascendant formula (corrected)
    # ASC = atan2(cos(LST), -(sin(LST)*cos(eps) + tan(lat)*sin(eps)))
    y = math.cos(LST_rad)
    x = -(math.sin(LST_rad) * math.cos(eps_rad) + math.tan(lat_rad) * math.sin(eps_rad))
    
    asc = math.degrees(math.atan2(y, x))
    asc = normalize_angle(asc)
    
    return asc


def calculate_mc(jd: float, longitude: float) -> float:
    """Calculate the Midheaven (MC)."""
    LST = calculate_sidereal_time(jd, longitude)
    LST_rad = math.radians(LST)
    
    eps = calculate_obliquity(jd)
    eps_rad = math.radians(eps)
    
    mc = math.degrees(math.atan2(math.sin(LST_rad), math.cos(LST_rad) * math.cos(eps_rad)))
    mc = normalize_angle(mc)
    
    return mc


def _placidus_intermediate(ramc: float, eps: float, lat: float,
                           fraction: float, above_horizon: bool) -> float:
    """
    Iteratively solve one Placidus intermediate cusp (tropical longitude).

    The cusp is the ecliptic point whose right ascension lies `fraction` of its
    OWN semi-arc away from the meridian (MC for houses 11/12, IC for 2/3), so
    the semi-arc depends on the cusp's declination and is found by iteration.

    Args:
        ramc: Right ascension of the MC (= local sidereal time), degrees
        eps: Obliquity of the ecliptic, degrees
        lat: Geographic latitude, degrees
        fraction: 1/3 or 2/3 of the semi-arc
        above_horizon: True for houses 11/12 (diurnal arc), False for 2/3 (nocturnal arc)
    """
    eps_rad = math.radians(eps)
    lat_rad = math.radians(lat)
    ra = ramc + 30.0 if above_horizon else ramc + 150.0  # first guess
    lon = 0.0

    for _ in range(50):
        ra_rad = math.radians(ra)
        lon = math.atan2(math.sin(ra_rad), math.cos(ra_rad) * math.cos(eps_rad))
        decl = math.asin(math.sin(eps_rad) * math.sin(lon))
        x = -math.tan(lat_rad) * math.tan(decl)
        if abs(x) >= 1.0:
            raise ValueError(
                "Placidus houses are undefined at this latitude (circumpolar ecliptic point)"
            )
        dsa = math.degrees(math.acos(x))            # diurnal semi-arc
        if above_horizon:
            new_ra = ramc + fraction * dsa          # MC -> ASC side
        else:
            new_ra = ramc + 180.0 - fraction * (180.0 - dsa)  # IC side (nocturnal arc)
        if abs(new_ra - ra) < 1e-10:
            ra = new_ra
            break
        ra = new_ra

    ra_rad = math.radians(ra)
    lon = math.atan2(math.sin(ra_rad), math.cos(ra_rad) * math.cos(eps_rad))
    return normalize_angle(math.degrees(lon))


def calculate_placidus_cusps(jd: float, latitude: float, longitude: float) -> list:
    """
    Calculate house cusps using the Placidus (semi-arc) system.

    Cusps 1 (ASC) and 10 (MC) are the angles. Cusps 11, 12, 2 and 3 are solved
    by trisecting the diurnal / nocturnal semi-arcs in right ascension; cusps
    4-9 are the opposites of 10, 11, 12, 1, 2, 3.

    Returns list of 12 house cusps in tropical longitude.
    """
    asc = calculate_ascendant(jd, latitude, longitude)
    mc = calculate_mc(jd, longitude)
    ramc = calculate_sidereal_time(jd, longitude)
    eps = calculate_obliquity(jd)

    c11 = _placidus_intermediate(ramc, eps, latitude, 1.0 / 3.0, True)
    c12 = _placidus_intermediate(ramc, eps, latitude, 2.0 / 3.0, True)
    c2 = _placidus_intermediate(ramc, eps, latitude, 2.0 / 3.0, False)
    c3 = _placidus_intermediate(ramc, eps, latitude, 1.0 / 3.0, False)

    return [
        asc,                          # 1
        c2,                           # 2
        c3,                           # 3
        normalize_angle(mc + 180),    # 4 (IC)
        normalize_angle(c11 + 180),   # 5
        normalize_angle(c12 + 180),   # 6
        normalize_angle(asc + 180),   # 7 (DSC)
        normalize_angle(c2 + 180),    # 8
        normalize_angle(c3 + 180),    # 9
        mc,                           # 10
        c11,                          # 11
        c12,                          # 12
    ]


def format_degrees_dms(degrees: float) -> str:
    """Format decimal degrees to degrees-minutes-seconds string."""
    deg = int(degrees)
    min_decimal = abs(degrees - deg) * 60
    minutes = int(min_decimal)
    seconds = (min_decimal - minutes) * 60
    
    return f"{deg}°{minutes:02d}'{seconds:05.2f}\""
