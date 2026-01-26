"""
KP New Ayanamsa Calculation Module

Implements the exact KP New Ayanamsa formula developed by Prof. K. Balachandran
as published in KP & Astrology Year Book 2003.

Formula: NKPA = B + [T * P + (T² * A)] / 3600

Where:
- B = Base value at Jan 1, 1900 = 22°22'15.7"
- T = Years since 1900
- P = Newcomb's precession rate = 50.2388475"/year
- A = Annual adjustment = 0.000111"/year²
"""

from app.services.astronomy import date_to_julian_day, julian_day_to_date, format_degrees_dms


# KP New Ayanamsa Constants (Prof. K. Balachandran)
BASE_YEAR = 1900
BASE_AYANAMSA_DEG = 22
BASE_AYANAMSA_MIN = 22
BASE_AYANAMSA_SEC = 15.7
BASE_AYANAMSA = BASE_AYANAMSA_DEG + BASE_AYANAMSA_MIN / 60.0 + BASE_AYANAMSA_SEC / 3600.0

# Precession constants
PRECESSION_RATE = 50.2388475  # arc-seconds per year (Newcomb's)
ANNUAL_ADJUSTMENT = 0.000111  # arc-seconds per year squared


def julian_day_to_year_fraction(jd: float) -> float:
    """
    Convert Julian Day to year with decimal fraction.
    
    Args:
        jd: Julian Day Number
        
    Returns:
        Year as decimal (e.g., 2002.298)
    """
    year, month, day, hour = julian_day_to_date(jd)
    
    # Calculate day of year
    jan1_jd = date_to_julian_day(year, 1, 1, 0, 0, 0.0, 0.0)
    day_of_year = jd - jan1_jd
    
    # Days in year (account for leap year)
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        days_in_year = 366.0
    else:
        days_in_year = 365.0
    
    return year + day_of_year / days_in_year


def calculate_kp_new_ayanamsa(jd: float) -> float:
    """
    Calculate the KP New Ayanamsa for a given Julian Day.
    
    This implements the exact formula from Prof. K. Balachandran:
    NKPA = B + [T * P + (T² * A)] / 3600
    
    Args:
        jd: Julian Day Number
        
    Returns:
        Ayanamsa value in degrees
    """
    # Get year with fraction
    year_fraction = julian_day_to_year_fraction(jd)
    
    # T = Years since 1900
    t = year_fraction - BASE_YEAR
    
    # Calculate precession correction in arc-seconds
    precession_arcsec = t * PRECESSION_RATE + (t * t * ANNUAL_ADJUSTMENT)
    
    # Convert to degrees and add to base
    precession_deg = precession_arcsec / 3600.0
    
    ayanamsa = BASE_AYANAMSA + precession_deg
    
    return ayanamsa


def calculate_ayanamsa_for_date(date_str: str, time_str: str = "00:00", 
                                 timezone: float = 0.0) -> dict:
    """
    Calculate KP New Ayanamsa for a given date string.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        time_str: Time in HH:MM format (24-hour)
        timezone: Timezone offset from UTC
        
    Returns:
        Dictionary with ayanamsa details
    """
    # Parse date
    date_parts = date_str.split("-")
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    
    # Parse time
    time_parts = time_str.split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    
    # Calculate Julian Day
    jd = date_to_julian_day(year, month, day, hour, minute, 0.0, timezone)
    
    # Calculate ayanamsa
    ayanamsa = calculate_kp_new_ayanamsa(jd)
    
    # Convert to DMS
    deg = int(ayanamsa)
    min_decimal = (ayanamsa - deg) * 60
    minutes = int(min_decimal)
    seconds = (min_decimal - minutes) * 60
    
    return {
        "julian_day": jd,
        "ayanamsa_decimal": round(ayanamsa, 6),
        "ayanamsa_dms": f"{deg}°{minutes:02d}'{seconds:05.2f}\"",
        "degrees": deg,
        "minutes": minutes,
        "seconds": round(seconds, 2)
    }
