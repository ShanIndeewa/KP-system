"""
KP Horary Number System (1-249)

This module implements the KP Horary chart calculation system based on
the 1-249 number system. Each horary number corresponds to a specific
Ascendant degree determined by Sub Lord boundaries.

The system works as follows:
1. The zodiac (360°) is divided into 243 sub-divisions
2. Each sub-division has a unique Sign-Star-Sub combination
3. User provides a horary number (1-249)
4. System finds the time when Ascendant matches that degree
5. Full chart is calculated for that time

Author: KP Astrology Backend
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

from app.core.kp_data import (
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_PERIODS,
    NAKSHATRAS,
    ZODIAC_SIGNS
)
from app.services.sublord import (
    get_sign_star_sub,
    normalize_longitude,
    NAKSHATRA_SPAN,
    TOTAL_DASHA_YEARS
)


# =============================================================================
# HORARY TABLE GENERATION
# =============================================================================

# Pre-computed horary table: horary_number -> start_longitude
HORARY_TABLE: Dict[int, float] = {}

# Detailed horary info: horary_number -> {longitude, sign_lord, star_lord, sub_lord}
HORARY_INFO: Dict[int, Dict] = {}


def generate_horary_table() -> Dict[int, float]:
    """
    Generate the 1-249 horary number table using mathematical calculation.
    
    The table maps each horary number to its starting longitude in the zodiac.
    There are exactly 243 sub-divisions (27 nakshatras × 9 subs each).
    
    Mathematical approach:
    - Each nakshatra spans 13°20' (800 arc-minutes)
    - Each nakshatra has 9 subs proportional to Vimshottari periods
    - Sub boundaries can be calculated directly without iteration
    
    Returns:
        Dict mapping horary number (1-243) to starting longitude
    """
    global HORARY_TABLE, HORARY_INFO
    
    if HORARY_TABLE:
        return HORARY_TABLE
    
    horary_table = {}
    horary_info = {}
    
    current_horary = 1
    
    # Iterate through all 27 nakshatras
    for nak_index in range(27):
        nakshatra = NAKSHATRAS[nak_index]
        nak_start = nak_index * NAKSHATRA_SPAN
        star_lord = nakshatra["lord"]
        
        # Find starting index in Vimshottari order for this nakshatra's lord
        start_sub_index = VIMSHOTTARI_ORDER.index(star_lord)
        
        # Calculate each of the 9 subs within this nakshatra
        sub_position = 0.0
        for sub_i in range(9):
            planet_index = (start_sub_index + sub_i) % 9
            sub_lord = VIMSHOTTARI_ORDER[planet_index]
            sub_period = VIMSHOTTARI_PERIODS[sub_lord]
            
            # Sub span in degrees
            sub_span = (sub_period / TOTAL_DASHA_YEARS) * NAKSHATRA_SPAN
            
            # Calculate absolute longitude for this sub
            abs_start = nak_start + sub_position
            abs_end = abs_start + sub_span
            
            # Check for sign boundary crossing (multiples of 30)
            # Find next multiple of 30 > abs_start
            # Use epsilon for float comparison to avoid issues at exact boundaries
            next_boundary = (int(abs_start / 30) + 1) * 30.0
            
            # Process sub interval(s)
            intervals = []
            
            if next_boundary < abs_end - 0.000001:
                # It crosses a boundary! Split into two parts.
                intervals.append((abs_start, next_boundary))
                intervals.append((next_boundary, abs_end))
            else:
                # No crossing, just one interval
                intervals.append((abs_start, abs_end))
                
            for interval_start, interval_end in intervals:
                # Determine sign for this interval
                mid_point = (interval_start + interval_end) / 2
                sign_index = int(mid_point / 30) % 12
                current_sign = ZODIAC_SIGNS[sign_index]
                
                # Store in horary table
                horary_table[current_horary] = interval_start
                horary_info[current_horary] = {
                    "start_longitude": interval_start,
                    "end_longitude": interval_end,
                    "sign_lord": current_sign["lord"],
                    "star_lord": star_lord,
                    "sub_lord": sub_lord,
                    "sign": current_sign["name"],
                    "nakshatra": nakshatra["name"]
                }
                
                current_horary += 1
            
            sub_position += sub_span
            
    HORARY_TABLE = horary_table
    HORARY_INFO = horary_info
    
    return horary_table


def _find_exact_boundary(lo: float, hi: float, precision: float = 0.000001) -> float:
    """
    Binary search to find exact sub lord boundary between lo and hi.
    
    Args:
        lo: Lower longitude (where previous sub lord exists)
        hi: Higher longitude (where new sub lord exists)
        precision: Search precision in degrees
        
    Returns:
        Exact longitude where sub lord changes
    """
    lo_info = get_sign_star_sub(lo)
    target_sub = get_sign_star_sub(hi)["sub_lord"]
    
    while hi - lo > precision:
        mid = (lo + hi) / 2
        mid_info = get_sign_star_sub(mid)
        
        if mid_info["sub_lord"] == target_sub:
            hi = mid
        else:
            lo = mid
    
    return hi


def get_horary_degree(horary_number: int) -> float:
    """
    Get the Ascendant degree for a given horary number.
    
    Args:
        horary_number: Number between 1 and 249
        
    Returns:
        Starting longitude for that horary number
        
    Raises:
        ValueError: If horary number is out of range
    """
    if horary_number < 1 or horary_number > 249:
        raise ValueError(f"Horary number must be between 1 and 249, got {horary_number}")
    
    if not HORARY_TABLE:
        generate_horary_table()
    
    return HORARY_TABLE[horary_number]


def get_horary_info(horary_number: int) -> Dict:
    """
    Get detailed information for a horary number.
    
    Args:
        horary_number: Number between 1 and 249
        
    Returns:
        Dict with start_longitude, sign_lord, star_lord, sub_lord, sign, nakshatra
    """
    if horary_number < 1 or horary_number > 249:
        raise ValueError(f"Horary number must be between 1 and 249, got {horary_number}")
    
    if not HORARY_INFO:
        generate_horary_table()
    
    return HORARY_INFO[horary_number]


# =============================================================================
# TIME FINDER ALGORITHM
# =============================================================================

def find_time_for_ascendant(
    target_longitude: float,
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    timezone: float = 5.5,
    precision_seconds: int = 1
) -> Optional[str]:
    """
    Find the time on a given date when the Ascendant matches target longitude.
    
    Uses binary search to find the exact time. The Ascendant moves through
    the entire zodiac (360°) in approximately 24 hours with varying speed.
    
    Algorithm:
    1. Start with search range 00:00:00 to 23:59:59
    2. Calculate Ascendant at both ends and middle
    3. Handle zodiac wrap-around (360° to 0°)
    4. Binary search until precision reached
    
    Args:
        target_longitude: Target Ascendant degree (0-360)
        year, month, day: Date for calculation
        latitude, longitude: Geographic coordinates
        timezone: Timezone offset from UTC
        precision_seconds: Target precision in seconds
        
    Returns:
        Time string in "HH:MM:SS" format, or None if not found
    """
    from app.services.astronomy import calculate_ascendant
    
    target = normalize_longitude(target_longitude)
    
    # Search range in seconds from midnight
    low = 0  # 00:00:00
    high = 86399  # 23:59:59
    
    # First check if target is achievable on this date
    # Get Ascendant at start and end of day
    asc_start = _get_ascendant_at_time(year, month, day, 0, 0, 0, latitude, longitude, timezone)
    asc_end = _get_ascendant_at_time(year, month, day, 23, 59, 59, latitude, longitude, timezone)
    
    # Try multiple search passes (for zodiac wrap-around handling)
    result = _binary_search_ascendant(
        target, year, month, day, latitude, longitude, timezone, 
        low, high, precision_seconds
    )
    
    if result is not None:
        seconds = result
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    return None


def _get_ascendant_at_time(
    year: int, month: int, day: int,
    hour: int, minute: int, second: int,
    latitude: float, longitude: float,
    timezone: float
) -> float:
    """
    Calculate Ascendant at a specific date/time/location.
    
    Returns:
        Tropical Ascendant longitude (0-360)
    """
    from app.services.astronomy import calculate_ascendant, date_to_julian_day
    
    # First convert date/time to Julian Day
    jd = date_to_julian_day(year, month, day, hour, minute, second, timezone)
    
    # calculate_ascendant takes (jd, latitude, longitude)
    return calculate_ascendant(jd, latitude, longitude)


def _binary_search_ascendant(
    target: float,
    year: int, month: int, day: int,
    latitude: float, longitude: float,
    timezone: float,
    low: int, high: int,
    precision: int
) -> Optional[int]:
    """
    Binary search for time when Ascendant matches target.
    
    Returns:
        Seconds from midnight, or None if not found
    """
    best_match = None
    best_diff = float('inf')
    
    # Use iterative approach with narrowing window
    iterations = 0
    max_iterations = 50
    
    while high - low > precision and iterations < max_iterations:
        iterations += 1
        
        # Check multiple points within the range
        low_time = _seconds_to_hms(low)
        high_time = _seconds_to_hms(high)
        mid = (low + high) // 2
        mid_time = _seconds_to_hms(mid)
        
        asc_low = _get_ascendant_at_time(year, month, day, *low_time, latitude, longitude, timezone)
        asc_high = _get_ascendant_at_time(year, month, day, *high_time, latitude, longitude, timezone)
        asc_mid = _get_ascendant_at_time(year, month, day, *mid_time, latitude, longitude, timezone)
        
        # Calculate angular differences (handling wrap-around)
        diff_low = _angular_difference(target, asc_low)
        diff_high = _angular_difference(target, asc_high)
        diff_mid = _angular_difference(target, asc_mid)
        
        # Track best match
        if diff_low < best_diff:
            best_diff = diff_low
            best_match = low
        if diff_mid < best_diff:
            best_diff = diff_mid
            best_match = mid
        if diff_high < best_diff:
            best_diff = diff_high
            best_match = high
        
        # If we found exact match (within tolerance)
        if best_diff < 0.01:  # Within 0.01 degrees (about 36 arc-seconds)
            return best_match
        
        # Determine which half contains the target
        # The Ascendant generally moves forward (increases) as time passes
        # But it can wrap from 360 to 0
        
        # Check if target is in first or second half
        if _is_between_angles(target, asc_low, asc_mid):
            high = mid
        elif _is_between_angles(target, asc_mid, asc_high):
            low = mid
        else:
            # Target might be due to wrap-around
            # Refine around best match
            quarter = (high - low) // 4
            if best_match == low:
                high = low + quarter * 2
            elif best_match == high:
                low = high - quarter * 2
            else:
                low = max(0, best_match - quarter)
                high = min(86399, best_match + quarter)
    
    # Return best match if close enough
    if best_match is not None and best_diff < 0.5:  # Within 0.5 degrees
        return best_match
    
    return None


def _seconds_to_hms(seconds: int) -> Tuple[int, int, int]:
    """Convert seconds from midnight to (hour, minute, second)."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return hours, minutes, secs


def _angular_difference(a: float, b: float) -> float:
    """
    Calculate shortest angular difference between two angles.
    
    Returns value between 0 and 180.
    """
    diff = abs(a - b)
    if diff > 180:
        diff = 360 - diff
    return diff


def _is_between_angles(target: float, start: float, end: float) -> bool:
    """
    Check if target angle is between start and end (going forward).
    
    Handles wrap-around at 360°.
    """
    if start <= end:
        # Normal case: no wrap-around
        return start <= target <= end
    else:
        # Wrap-around case
        return target >= start or target <= end


# =============================================================================
# HORARY CHART CALCULATION
# =============================================================================

def calculate_horary_chart(
    horary_number: int,
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    timezone: float = 5.5,
    seed_hour: int = 12,
    seed_minute: int = 0
) -> Optional[Dict]:
    """
    Calculate a complete horary chart for the given horary number.
    
    This is the main entry point for horary calculations.
    
    Args:
        horary_number: KP horary number (1-249)
        year, month, day: Date of query
        latitude, longitude: Location coordinates
        timezone: Timezone offset from UTC
        seed_hour, seed_minute: Seed time (used as hint for search)
        
    Returns:
        Dict containing:
        - horary_number: The input number
        - target_ascendant: The target Ascendant degree
        - calculated_time: The found time string
        - horary_info: Sign/Star/Sub information
        - success: Boolean indicating if time was found
        
        Or None if calculation fails
    """
    try:
        # Get the target ascendant degree for this horary number
        target_longitude = get_horary_degree(horary_number)
        horary_details = get_horary_info(horary_number)
        
        # Find the time when Ascendant matches
        found_time = find_time_for_ascendant(
            target_longitude,
            year, month, day,
            latitude, longitude,
            timezone
        )
        
        if found_time is None:
            return {
                "success": False,
                "horary_number": horary_number,
                "target_ascendant": target_longitude,
                "calculated_time": None,
                "horary_info": horary_details,
                "error": "Could not find matching time on this date"
            }
        
        return {
            "success": True,
            "horary_number": horary_number,
            "target_ascendant": target_longitude,
            "calculated_time": found_time,
            "horary_info": horary_details,
            "date": f"{year:04d}-{month:02d}-{day:02d}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "horary_number": horary_number,
            "error": str(e)
        }


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_horary_table():
    """
    Pre-compute the horary table at module load.
    Call this during application startup for faster first request.
    """
    generate_horary_table()


# Generate table on module import (can be commented out for lazy loading)
# initialize_horary_table()
