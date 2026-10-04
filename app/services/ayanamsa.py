"""
KP Ayanamsa Calculation Module

Supports four ayanamsa calculation methods:
1. KP Old (KSK) - Original formula by K.S. Krishnamurti
2. KP New (Balachandran) - Enhanced formula by Prof. K. Balachandran (2003)
3. KP Khullar - S.P. Khullar's linear formula (zero year 292 AD)
4. Manual - User-provided custom ayanamsa value

Formula: Ayanamsa = B + [T * P + (T² * A)] / 3600

Where:
- B = Base value at Jan 1, 1900
- T = Years since 1900
- P = Newcomb's precession rate = 50.2388475"/year
- A = Annual adjustment = 0.000111"/year²

Both KP Old and KP New use the same precession formula,
but differ in their base values at Jan 1, 1900:
- KP Old (KSK): 22°22'00" (22.366667°)
- KP New (Balachandran): 22°22'15.7" (22.371028°)
"""

from enum import Enum
from typing import Optional
from app.services.astronomy import date_to_julian_day, julian_day_to_date, format_degrees_dms


class AyanamsaType(str, Enum):
    """Ayanamsa calculation type enumeration."""
    OLD = "old"      # KP Old (KSK) - Original
    NEW = "new"      # KP New (Balachandran) - Current standard
    KHULLAR = "khullar"  # KP Khullar (S.P. Khullar) - zero year 292 AD
    STRAIGHT = "straight"  # KP Straight - TDB based, epoch J1900.0
    MANUAL = "manual"  # User-provided value


# =============================================================================
# KP New Ayanamsa Constants (Prof. K. Balachandran)
# =============================================================================
BASE_YEAR = 1900

# New KP: Base at Jan 1, 1900 = 22°22'15.7"
BASE_NEW_DEG = 22
BASE_NEW_MIN = 22
BASE_NEW_SEC = 15.7
BASE_NEW_AYANAMSA = BASE_NEW_DEG + BASE_NEW_MIN / 60.0 + BASE_NEW_SEC / 3600.0

# Old KP (KSK): Base at Jan 1, 1900 = 22°22'00"
BASE_OLD_DEG = 22
BASE_OLD_MIN = 22
BASE_OLD_SEC = 0.0
BASE_OLD_AYANAMSA = BASE_OLD_DEG + BASE_OLD_MIN / 60.0 + BASE_OLD_SEC / 3600.0

# Precession constants (same for both)
PRECESSION_RATE = 50.2388475  # arc-seconds per year (Newcomb's)
ANNUAL_ADJUSTMENT = 0.000111  # arc-seconds per year squared

# KP Khullar: linear precession from zero year 292 AD (+ 261/365 year offset)
KHULLAR_ZERO_YEAR = 292
KHULLAR_OFFSET = 261 / 365.0


# KP Straight: base at J1900.0 plus quadratic precession (arc-seconds)
J1900_JD = 2415020.0
# Original base 22.4512382555 reduced by 3.7403" (0.00103896 deg) so the Raj chart
# (1972-11-29 05:03:50 IST) gives 23°28'03", matching the reference software.
STRAIGHT_BASE_DEG = 22.4501992955
STRAIGHT_RATE = 50.22512820   # arc-seconds per Julian year
STRAIGHT_ACCEL = 0.00006660   # arc-seconds per Julian year squared

_timescale = None


def julian_day_to_tdb(jd_ut: float) -> float:
    """Convert a UT Julian Day to TDB Julian Day (Skyfield's built-in Delta T)."""
    global _timescale
    if _timescale is None:
        from skyfield.api import load
        _timescale = load.timescale()
    return float(_timescale.ut1_jd(jd_ut).tdb)


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
    Calculate the KP New Ayanamsa (Balachandran) for a given Julian Day.
    
    This implements the formula from Prof. K. Balachandran:
    NKPA = B + [T * P + (T² * A)] / 3600
    
    Base at Jan 1, 1900: 22°22'15.7"
    
    Args:
        jd: Julian Day Number
        
    Returns:
        Ayanamsa value in degrees
    """
    year_fraction = julian_day_to_year_fraction(jd)
    t = year_fraction - BASE_YEAR
    
    # Calculate precession correction in arc-seconds
    precession_arcsec = t * PRECESSION_RATE + (t * t * ANNUAL_ADJUSTMENT)
    
    # Convert to degrees and add to base
    precession_deg = precession_arcsec / 3600.0
    
    return BASE_NEW_AYANAMSA + precession_deg


def calculate_kp_old_ayanamsa(jd: float) -> float:
    """
    Calculate the KP Old Ayanamsa (KSK) for a given Julian Day.
    
    This implements the original formula by K.S. Krishnamurti:
    OKPA = B + [T * P + (T² * A)] / 3600
    
    Base at Jan 1, 1900: 22°22'00"
    
    Args:
        jd: Julian Day Number
        
    Returns:
        Ayanamsa value in degrees
    """
    year_fraction = julian_day_to_year_fraction(jd)
    t = year_fraction - BASE_YEAR
    
    # Calculate precession correction in arc-seconds
    precession_arcsec = t * PRECESSION_RATE + (t * t * ANNUAL_ADJUSTMENT)
    
    # Convert to degrees and add to base
    precession_deg = precession_arcsec / 3600.0
    
    return BASE_OLD_AYANAMSA + precession_deg


def calculate_kp_khullar_ayanamsa(jd: float) -> float:
    """
    Calculate the KP Khullar Ayanamsa (S.P. Khullar) for a given Julian Day.

    Formula: Ayanamsa = (P / 3600) * ((YEAR - 292) + 261/365 + day_fraction)
    where P = 50.2388475"/year and the zero year is 292 AD.
    Gives about 23°50'44" on Jan 1, 2000.

    Args:
        jd: Julian Day Number

    Returns:
        Ayanamsa value in degrees
    """
    year_fraction = julian_day_to_year_fraction(jd)
    return (PRECESSION_RATE / 3600.0) * ((year_fraction - KHULLAR_ZERO_YEAR) + KHULLAR_OFFSET)


def calculate_kp_straight_ayanamsa(jd: float) -> float:
    """
    Calculate the KP Straight Ayanamsa for a given (UT) Julian Day.

    dt   = (JD_TDB - J1900) / 365.25          # Julian years since J1900.0
    prec = 50.22512820 * dt + 0.00006660 * dt^2   # arc-seconds
    ayanamsa = STRAIGHT_BASE_DEG + prec / 3600    # base 22.4501992955 (calibrated), 8 decimals

    Args:
        jd: Julian Day Number (UT, as produced by date_to_julian_day)

    Returns:
        Ayanamsa value in degrees
    """
    dt = (julian_day_to_tdb(jd) - J1900_JD) / 365.25
    prec = STRAIGHT_RATE * dt + STRAIGHT_ACCEL * dt * dt
    return round(STRAIGHT_BASE_DEG + prec / 3600.0, 8)


def calculate_ayanamsa(jd: float,
                       ayanamsa_type: str = "new",
                       manual_value: Optional[float] = None) -> tuple[float, str]:
    """
    Unified ayanamsa calculation supporting all three methods.
    
    Args:
        jd: Julian Day Number
        ayanamsa_type: Type of ayanamsa - 'old', 'new', 'khullar', 'straight' or 'manual'
        manual_value: Custom ayanamsa value (required when type='manual')
        
    Returns:
        Tuple of (ayanamsa_value, ayanamsa_type_label)
    """
    ayanamsa_type = ayanamsa_type.lower()
    
    if ayanamsa_type == AyanamsaType.MANUAL.value:
        if manual_value is None:
            raise ValueError("manual_ayanamsa value is required when ayanamsa_type is 'manual'")
        return (manual_value, "Manual")
    
    elif ayanamsa_type == AyanamsaType.OLD.value:
        return (calculate_kp_old_ayanamsa(jd), "KP Old (KSK)")

    elif ayanamsa_type == AyanamsaType.KHULLAR.value:
        return (calculate_kp_khullar_ayanamsa(jd), "KP Khullar")

    elif ayanamsa_type == AyanamsaType.STRAIGHT.value:
        return (calculate_kp_straight_ayanamsa(jd), "KP Straight")
    
    else:  # Default to new
        return (calculate_kp_new_ayanamsa(jd), "KP New (Balachandran)")


def calculate_ayanamsa_for_date(date_str: str, time_str: str = "00:00", 
                                 timezone: float = 0.0,
                                 ayanamsa_type: str = "new",
                                 manual_value: Optional[float] = None) -> dict:
    """
    Calculate ayanamsa for a given date string.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        time_str: Time in HH:MM format (24-hour)
        timezone: Timezone offset from UTC
        ayanamsa_type: 'old', 'new', or 'manual'
        manual_value: Custom ayanamsa value (when type='manual')
        
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
    
    # Calculate ayanamsa using unified function
    ayanamsa, type_label = calculate_ayanamsa(jd, ayanamsa_type, manual_value)
    
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
        "seconds": round(seconds, 2),
        "type": type_label
    }

