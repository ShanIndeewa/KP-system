"""
House Cusp Calculation Module (Bhawa/Bhava)

Calculates the 12 house cusps using Placidus (Semi-Arc) system
as specified by KP Astrology methodology.

Each house cusp includes:
- Sign Lord
- Star Lord (Nakshatra Lord)
- Sub Lord
"""

from typing import List, Dict
from app.services.astronomy import (
    calculate_placidus_cusps,
    calculate_ascendant as calc_asc,
    calculate_mc,
    normalize_angle
)
from app.services.sublord import get_sign_star_sub


def calculate_house_cusps(jd: float, latitude: float, longitude: float, 
                          ayanamsa: float) -> List[Dict]:
    """
    Calculate the 12 house cusps using Placidus system.
    
    In KP Astrology, Bhawa (house) cusps are calculated using Placidus
    (Semi-Arc) system. Each cusp then has its Sign/Star/Sub lords calculated.
    
    Args:
        jd: Julian Day Number
        latitude: Geographic latitude in decimal degrees
        longitude: Geographic longitude in decimal degrees  
        ayanamsa: KP New Ayanamsa value in degrees
        
    Returns:
        List of 12 house cusp dictionaries with full lordship details
    """
    # Calculate tropical house cusps using Placidus system
    tropical_cusps = calculate_placidus_cusps(jd, latitude, longitude)
    
    house_cusps = []
    
    for house_num in range(1, 13):
        tropical_cusp = tropical_cusps[house_num - 1]  # 0-indexed
        
        # Apply ayanamsa to get sidereal cusp
        sidereal_cusp = normalize_angle(tropical_cusp - ayanamsa)
        
        # Get sign/star/sub details
        details = get_sign_star_sub(sidereal_cusp)
        
        cusp_data = {
            "house": house_num,
            "bhawa": house_num,  # Bhawa is the Sanskrit term for house
            "longitude": round(sidereal_cusp, 6),
            "longitude_dms": details["longitude_dms"],
            "tropical_longitude": round(tropical_cusp, 6),
            "sign": details["sign"]["name"],
            "sign_lord": details["sign"]["lord"],
            "star": details["star"]["name"],
            "star_lord": details["star"]["lord"],
            "sub_lord": details["sub_lord"],
            "sub_sub_lord": details.get("sub_sub_lord", ""),
            "pada": details["star"]["pada"]
        }
        
        house_cusps.append(cusp_data)
    
    return house_cusps


def calculate_ascendant(jd: float, latitude: float, longitude: float,
                        ayanamsa: float) -> Dict:
    """
    Calculate the Ascendant (Lagna) with full lordship details.
    
    Args:
        jd: Julian Day Number
        latitude: Geographic latitude
        longitude: Geographic longitude
        ayanamsa: KP New Ayanamsa value
        
    Returns:
        Ascendant details dictionary
    """
    tropical_asc = calc_asc(jd, latitude, longitude)
    sidereal_asc = normalize_angle(tropical_asc - ayanamsa)
    
    details = get_sign_star_sub(sidereal_asc)
    
    return {
        "name": "Ascendant",
        "longitude": round(sidereal_asc, 6),
        "longitude_dms": details["longitude_dms"],
        "sign": details["sign"]["name"],
        "sign_lord": details["sign"]["lord"],
        "star": details["star"]["name"],
        "star_lord": details["star"]["lord"],
        "sub_lord": details["sub_lord"],
        "sub_sub_lord": details.get("sub_sub_lord", "")
    }


def calculate_midheaven(jd: float, latitude: float, longitude: float,
                        ayanamsa: float) -> Dict:
    """
    Calculate the Midheaven (MC - Medium Coeli) with full lordship details.
    
    Args:
        jd: Julian Day Number
        latitude: Geographic latitude
        longitude: Geographic longitude
        ayanamsa: KP New Ayanamsa value
        
    Returns:
        Midheaven details dictionary
    """
    tropical_mc = calculate_mc(jd, longitude)
    sidereal_mc = normalize_angle(tropical_mc - ayanamsa)
    
    details = get_sign_star_sub(sidereal_mc)
    
    return {
        "name": "Midheaven",
        "longitude": round(sidereal_mc, 6),
        "longitude_dms": details["longitude_dms"],
        "sign": details["sign"]["name"],
        "sign_lord": details["sign"]["lord"],
        "star": details["star"]["name"],
        "star_lord": details["star"]["lord"],
        "sub_lord": details["sub_lord"],
        "sub_sub_lord": details.get("sub_sub_lord", "")
    }


def get_bhawa_table(jd: float, latitude: float, longitude: float,
                    ayanamsa: float) -> Dict:
    """
    Generate a complete Bhawa (house) table with all details.
    
    This is specifically for KP astrology analysis, providing
    all house cusps with their Sign/Star/Sub lordships for
    predictive analysis.
    
    Args:
        jd: Julian Day Number
        latitude: Geographic latitude
        longitude: Geographic longitude
        ayanamsa: KP New Ayanamsa value
        
    Returns:
        Complete bhawa table dictionary
    """
    house_cusps = calculate_house_cusps(jd, latitude, longitude, ayanamsa)
    ascendant = calculate_ascendant(jd, latitude, longitude, ayanamsa)
    midheaven = calculate_midheaven(jd, latitude, longitude, ayanamsa)
    
    return {
        "ascendant": ascendant,
        "midheaven": midheaven,
        "houses": house_cusps,
        "house_system": "Placidus"
    }


def get_house_spans(jd: float, latitude: float, longitude: float,
                    ayanamsa: float) -> List[Dict]:
    """
    Calculate the span of each house (from cusp to next cusp).
    
    Useful for determining which house a planet occupies.
    
    Args:
        jd: Julian Day Number
        latitude: Geographic latitude
        longitude: Geographic longitude
        ayanamsa: KP New Ayanamsa value
        
    Returns:
        List of house spans with start and end longitudes
    """
    tropical_cusps = calculate_placidus_cusps(jd, latitude, longitude)
    
    spans = []
    
    for i in range(12):
        start_cusp = normalize_angle(tropical_cusps[i] - ayanamsa)
        end_cusp = normalize_angle(tropical_cusps[(i + 1) % 12] - ayanamsa)
        
        spans.append({
            "house": i + 1,
            "start": round(start_cusp, 6),
            "end": round(end_cusp, 6)
        })
    
    return spans


def find_planet_house(planet_longitude: float, house_spans: List[Dict]) -> int:
    """
    Find which house a planet occupies based on its longitude.
    
    Args:
        planet_longitude: Sidereal longitude of the planet
        house_spans: List of house spans from get_house_spans()
        
    Returns:
        House number (1-12)
    """
    planet_longitude = normalize_angle(planet_longitude)
    
    for span in house_spans:
        start = span["start"]
        end = span["end"]
        
        # Handle wrap-around at 360/0 degrees
        if end < start:
            # House spans across 0 degrees
            if planet_longitude >= start or planet_longitude < end:
                return span["house"]
        else:
            if start <= planet_longitude < end:
                return span["house"]
    
    # Default to house 1 if not found (shouldn't happen)
    return 1
