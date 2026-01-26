"""
KP Sub-Lord Calculation Module

Implements the core KP system calculation for Sign Lord, Star Lord, and Sub Lord.

The hierarchy:
1. Sign (Rashi): 30 degrees each, 12 signs
2. Star (Nakshatra): 13°20' each, 27 stars
3. Sub: Nakshatra divided into 9 parts based on Vimshottari Dasha proportions

The Sub division starts from the Star Lord and follows Vimshottari Dasha order.
"""

from typing import Dict, Optional
from app.core.kp_data import (
    ZODIAC_SIGNS, 
    NAKSHATRAS, 
    VIMSHOTTARI_ORDER, 
    VIMSHOTTARI_PERIODS,
    TOTAL_DASHA_YEARS,
    NAKSHATRA_SPAN
)


def normalize_longitude(longitude: float) -> float:
    """
    Normalize longitude to 0-360 range.
    
    Args:
        longitude: Any longitude value
        
    Returns:
        Longitude normalized to 0-360
    """
    while longitude < 0:
        longitude += 360.0
    while longitude >= 360:
        longitude -= 360.0
    return longitude


def get_sign(longitude: float) -> Dict:
    """
    Get the zodiac sign for a given sidereal longitude.
    
    Args:
        longitude: Sidereal longitude (0-360)
        
    Returns:
        Dict with sign details including name and lord
    """
    longitude = normalize_longitude(longitude)
    sign_index = int(longitude / 30.0)
    
    sign = ZODIAC_SIGNS[sign_index]
    position_in_sign = longitude - (sign_index * 30.0)
    
    return {
        "index": sign["index"],
        "name": sign["name"],
        "lord": sign["lord"],
        "position_in_sign": round(position_in_sign, 6)
    }


def get_star(longitude: float) -> Dict:
    """
    Get the Nakshatra (Star) for a given sidereal longitude.
    
    Args:
        longitude: Sidereal longitude (0-360)
        
    Returns:
        Dict with nakshatra details including name, lord, and pada
    """
    longitude = normalize_longitude(longitude)
    star_index = int(longitude / NAKSHATRA_SPAN)
    
    # Handle edge case at 360
    if star_index >= 27:
        star_index = 0
    
    nakshatra = NAKSHATRAS[star_index]
    position_in_star = longitude - (star_index * NAKSHATRA_SPAN)
    
    # Calculate Pada (quarter) - each pada is 3°20' = 3.333... degrees
    pada_span = NAKSHATRA_SPAN / 4.0
    pada = int(position_in_star / pada_span) + 1
    if pada > 4:
        pada = 4
    
    return {
        "index": nakshatra["index"],
        "name": nakshatra["name"],
        "lord": nakshatra["lord"],
        "pada": pada,
        "position_in_star": round(position_in_star, 6)
    }


def get_sub_lord(longitude: float) -> Dict:
    """
    Get the Sub Lord for a given sidereal longitude.
    
    The Sub division divides each Nakshatra (13°20' = 800 arc-minutes) into
    9 parts proportional to Vimshottari Dasha periods. The division starts
    from the Star Lord of that Nakshatra.
    
    Args:
        longitude: Sidereal longitude (0-360)
        
    Returns:
        Dict with sub lord details
    """
    longitude = normalize_longitude(longitude)
    
    # Get the star first
    star_index = int(longitude / NAKSHATRA_SPAN)
    if star_index >= 27:
        star_index = 0
    
    nakshatra = NAKSHATRAS[star_index]
    star_lord = nakshatra["lord"]
    
    # Position within the nakshatra (in degrees)
    position_in_star = longitude - (star_index * NAKSHATRA_SPAN)
    
    # Find starting index in Vimshottari order for this star lord
    start_index = VIMSHOTTARI_ORDER.index(star_lord)
    
    # Calculate sub spans proportionally
    # Each nakshatra is 800 arc-minutes (13°20')
    # Sub span for each planet = (dasha period / 120) * 13.333... degrees
    
    accumulated = 0.0
    sub_lord = None
    sub_start = 0.0
    sub_end = 0.0
    
    for i in range(9):
        planet_index = (start_index + i) % 9
        planet = VIMSHOTTARI_ORDER[planet_index]
        period = VIMSHOTTARI_PERIODS[planet]
        
        # Sub span in degrees
        sub_span = (period / TOTAL_DASHA_YEARS) * NAKSHATRA_SPAN
        
        if position_in_star < accumulated + sub_span:
            sub_lord = planet
            sub_start = accumulated
            sub_end = accumulated + sub_span
            break
        
        accumulated += sub_span
    
    # If somehow not found (shouldn't happen), use last one
    if sub_lord is None:
        sub_lord = VIMSHOTTARI_ORDER[(start_index + 8) % 9]
    
    position_in_sub = position_in_star - sub_start
    
    return {
        "lord": sub_lord,
        "position_in_sub": round(position_in_sub, 6)
    }


def get_sub_sub_lord(longitude: float) -> Dict:
    """
    Get the Sub-Sub Lord for a given sidereal longitude.
    
    This further divides the Sub portion into 9 parts based on Vimshottari
    proportions, starting from the Sub Lord.
    
    Args:
        longitude: Sidereal longitude (0-360)
        
    Returns:
        Dict with sub-sub lord details
    """
    longitude = normalize_longitude(longitude)
    
    # Get star and sub first
    star_index = int(longitude / NAKSHATRA_SPAN)
    if star_index >= 27:
        star_index = 0
    
    nakshatra = NAKSHATRAS[star_index]
    star_lord = nakshatra["lord"]
    
    # Position within the nakshatra
    position_in_star = longitude - (star_index * NAKSHATRA_SPAN)
    
    # Find starting index for sub calculation
    star_start_index = VIMSHOTTARI_ORDER.index(star_lord)
    
    # Find which sub we're in
    accumulated = 0.0
    sub_lord = None
    sub_start = 0.0
    sub_span_deg = 0.0
    
    for i in range(9):
        planet_index = (star_start_index + i) % 9
        planet = VIMSHOTTARI_ORDER[planet_index]
        period = VIMSHOTTARI_PERIODS[planet]
        
        sub_span = (period / TOTAL_DASHA_YEARS) * NAKSHATRA_SPAN
        
        if position_in_star < accumulated + sub_span:
            sub_lord = planet
            sub_start = accumulated
            sub_span_deg = sub_span
            break
        
        accumulated += sub_span
    
    if sub_lord is None:
        return {"lord": "Unknown"}
    
    # Now calculate sub-sub within this sub
    position_in_sub = position_in_star - sub_start
    sub_sub_start_index = VIMSHOTTARI_ORDER.index(sub_lord)
    
    accumulated_ss = 0.0
    sub_sub_lord = None
    
    for i in range(9):
        planet_index = (sub_sub_start_index + i) % 9
        planet = VIMSHOTTARI_ORDER[planet_index]
        period = VIMSHOTTARI_PERIODS[planet]
        
        # Sub-sub span within sub
        sub_sub_span = (period / TOTAL_DASHA_YEARS) * sub_span_deg
        
        if position_in_sub < accumulated_ss + sub_sub_span:
            sub_sub_lord = planet
            break
        
        accumulated_ss += sub_sub_span
    
    if sub_sub_lord is None:
        sub_sub_lord = VIMSHOTTARI_ORDER[(sub_sub_start_index + 8) % 9]
    
    return {
        "lord": sub_sub_lord
    }


def get_sign_star_sub(longitude: float, include_sub_sub: bool = True) -> Dict:
    """
    Get complete Sign, Star, and Sub Lord details for a longitude.
    
    This is the main utility function that returns all hierarchical
    lordship information for any sidereal longitude.
    
    Args:
        longitude: Sidereal longitude (0-360)
        include_sub_sub: Whether to include sub-sub lord calculation
        
    Returns:
        Complete dict with sign, star, sub (and optionally sub-sub) details
    """
    longitude = normalize_longitude(longitude)
    
    sign = get_sign(longitude)
    star = get_star(longitude)
    sub = get_sub_lord(longitude)
    
    result = {
        "longitude": round(longitude, 6),
        "longitude_dms": format_longitude_dms(longitude),
        "sign": {
            "name": sign["name"],
            "lord": sign["lord"],
            "position": round(sign["position_in_sign"], 4)
        },
        "star": {
            "name": star["name"],
            "lord": star["lord"],
            "pada": star["pada"]
        },
        "sub_lord": sub["lord"]
    }
    
    if include_sub_sub:
        sub_sub = get_sub_sub_lord(longitude)
        result["sub_sub_lord"] = sub_sub["lord"]
    
    return result


def format_longitude_dms(longitude: float) -> str:
    """
    Format longitude as sign-degrees-minutes-seconds.
    
    Args:
        longitude: Sidereal longitude (0-360)
        
    Returns:
        String like "15°32'45\" Aries" or "05°12'30\" Taurus"
    """
    longitude = normalize_longitude(longitude)
    
    # Get sign
    sign_index = int(longitude / 30.0)
    sign_name = ZODIAC_SIGNS[sign_index]["name"]
    
    # Position in sign
    pos_in_sign = longitude - (sign_index * 30.0)
    
    # Convert to DMS
    degrees = int(pos_in_sign)
    min_decimal = (pos_in_sign - degrees) * 60
    minutes = int(min_decimal)
    seconds = (min_decimal - minutes) * 60
    
    return f"{degrees:02d}°{minutes:02d}'{seconds:05.2f}\" {sign_name}"


def format_longitude_compact(longitude: float) -> str:
    """
    Format longitude in compact format for display.
    
    Args:
        longitude: Sidereal longitude (0-360)
        
    Returns:
        String like "Ar 15°32'" or "Ta 05°12'"
    """
    longitude = normalize_longitude(longitude)
    
    # Get sign abbreviation
    sign_abbrev = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
    sign_index = int(longitude / 30.0)
    
    # Position in sign
    pos_in_sign = longitude - (sign_index * 30.0)
    degrees = int(pos_in_sign)
    minutes = int((pos_in_sign - degrees) * 60)
    
    return f"{sign_abbrev[sign_index]} {degrees:02d}°{minutes:02d}'"
