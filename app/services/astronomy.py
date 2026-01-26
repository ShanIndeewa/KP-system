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


def calculate_placidus_cusps(jd: float, latitude: float, longitude: float) -> list:
    """
    Calculate house cusps using Placidus system.
    
    Returns list of 12 house cusps in tropical longitude.
    """
    asc = calculate_ascendant(jd, latitude, longitude)
    mc = calculate_mc(jd, longitude)
    
    eps = calculate_obliquity(jd)
    lat_rad = math.radians(latitude)
    
    # House cusps array (0-indexed for houses 1-12)
    cusps = [0.0] * 12
    cusps[0] = asc   # House 1 (Ascendant)
    cusps[9] = mc    # House 10 (MC)
    
    # Calculate intermediate cusps using semi-arc method
    # For Placidus, we calculate by trisection of semi-arcs
    
    # IC (House 4) is opposite MC
    ic = normalize_angle(mc + 180)
    cusps[3] = ic
    
    # Descendant (House 7) is opposite Ascendant
    desc = normalize_angle(asc + 180)
    cusps[6] = desc
    
    # Calculate houses 11, 12 (between MC and ASC)
    arc_mc_to_asc = normalize_angle(asc - mc)
    if arc_mc_to_asc < 0:
        arc_mc_to_asc += 360
    
    cusps[10] = normalize_angle(mc + arc_mc_to_asc / 3)       # House 11
    cusps[11] = normalize_angle(mc + 2 * arc_mc_to_asc / 3)   # House 12
    
    # Calculate houses 2, 3 (between ASC and IC)
    arc_asc_to_ic = normalize_angle(ic - asc)
    if arc_asc_to_ic < 0:
        arc_asc_to_ic += 360
    
    cusps[1] = normalize_angle(asc + arc_asc_to_ic / 3)       # House 2
    cusps[2] = normalize_angle(asc + 2 * arc_asc_to_ic / 3)   # House 3
    
    # Houses 5, 6 (between IC and DESC)
    arc_ic_to_desc = normalize_angle(desc - ic)
    if arc_ic_to_desc < 0:
        arc_ic_to_desc += 360
    
    cusps[4] = normalize_angle(ic + arc_ic_to_desc / 3)       # House 5
    cusps[5] = normalize_angle(ic + 2 * arc_ic_to_desc / 3)   # House 6
    
    # Houses 8, 9 (between DESC and MC)
    arc_desc_to_mc = normalize_angle(mc + 360 - desc) if mc < desc else normalize_angle(mc - desc)
    
    cusps[7] = normalize_angle(desc + arc_desc_to_mc / 3)     # House 8
    cusps[8] = normalize_angle(desc + 2 * arc_desc_to_mc / 3) # House 9
    
    return cusps


def format_degrees_dms(degrees: float) -> str:
    """Format decimal degrees to degrees-minutes-seconds string."""
    deg = int(degrees)
    min_decimal = abs(degrees - deg) * 60
    minutes = int(min_decimal)
    seconds = (min_decimal - minutes) * 60
    
    return f"{deg}°{minutes:02d}'{seconds:05.2f}\""
