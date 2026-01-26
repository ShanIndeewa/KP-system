"""
Planetary Position Calculation Module

Calculates planetary positions using pure Python astronomical algorithms
and applies KP New Ayanamsa to get sidereal positions.

Planets calculated:
- Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
- Rahu (Mean Node), Ketu (180° opposite to Rahu)
"""

from typing import List, Dict
from app.core.kp_data import PLANET_ORDER
from app.services.astronomy import (
    calculate_sun_position,
    calculate_moon_position,
    calculate_planet_position,
    calculate_rahu_position,
    normalize_angle
)
from app.services.sublord import get_sign_star_sub


def calculate_planet_positions(jd: float, ayanamsa: float) -> List[Dict]:
    """
    Calculate positions for all planets in sidereal zodiac.
    
    Args:
        jd: Julian Day Number
        ayanamsa: KP New Ayanamsa value in degrees
        
    Returns:
        List of planet position dictionaries
    """
    positions = []
    
    for planet_name in PLANET_ORDER:
        if planet_name == "Ketu":
            continue  # Ketu is added after Rahu
        
        # Calculate tropical longitude
        if planet_name == "Sun":
            tropical_longitude = calculate_sun_position(jd)
            is_retrograde = False
        elif planet_name == "Moon":
            tropical_longitude = calculate_moon_position(jd)
            is_retrograde = False
        elif planet_name == "Rahu":
            tropical_longitude = calculate_rahu_position(jd)
            is_retrograde = True  # Nodes are always retrograde
        else:
            tropical_longitude, is_retrograde = calculate_planet_position(jd, planet_name)
        
        # Apply ayanamsa to get sidereal longitude
        sidereal_longitude = normalize_angle(tropical_longitude - ayanamsa)
        
        # Get sign/star/sub details
        details = get_sign_star_sub(sidereal_longitude)
        
        position = {
            "name": planet_name,
            "longitude": round(sidereal_longitude, 6),
            "longitude_dms": details["longitude_dms"],
            "tropical_longitude": round(tropical_longitude, 6),
            "sign": details["sign"]["name"],
            "sign_lord": details["sign"]["lord"],
            "star": details["star"]["name"],
            "star_lord": details["star"]["lord"],
            "sub_lord": details["sub_lord"],
            "sub_sub_lord": details.get("sub_sub_lord", ""),
            "pada": details["star"]["pada"],
            "retrograde": is_retrograde
        }
        
        positions.append(position)
        
        # Add Ketu after Rahu (180° opposite)
        if planet_name == "Rahu":
            ketu_tropical = normalize_angle(tropical_longitude + 180.0)
            ketu_sidereal = normalize_angle(ketu_tropical - ayanamsa)
            ketu_details = get_sign_star_sub(ketu_sidereal)
            
            ketu_position = {
                "name": "Ketu",
                "longitude": round(ketu_sidereal, 6),
                "longitude_dms": ketu_details["longitude_dms"],
                "tropical_longitude": round(ketu_tropical, 6),
                "sign": ketu_details["sign"]["name"],
                "sign_lord": ketu_details["sign"]["lord"],
                "star": ketu_details["star"]["name"],
                "star_lord": ketu_details["star"]["lord"],
                "sub_lord": ketu_details["sub_lord"],
                "sub_sub_lord": ketu_details.get("sub_sub_lord", ""),
                "pada": ketu_details["star"]["pada"],
                "retrograde": True  # Nodes are always retrograde
            }
            
            positions.append(ketu_position)
    
    # Sort by the standard order
    order_map = {name: i for i, name in enumerate(PLANET_ORDER)}
    positions.sort(key=lambda x: order_map.get(x["name"], 99))
    
    return positions


def get_planet_position_simple(jd: float, planet_name: str, ayanamsa: float) -> Dict:
    """
    Get position for a single planet.
    
    Args:
        jd: Julian Day Number
        planet_name: Name of planet (Sun, Moon, etc.)
        ayanamsa: KP New Ayanamsa value
        
    Returns:
        Planet position dictionary
    """
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    
    if planet_name not in valid_planets:
        raise ValueError(f"Unknown planet: {planet_name}")
    
    if planet_name == "Sun":
        tropical_longitude = calculate_sun_position(jd)
    elif planet_name == "Moon":
        tropical_longitude = calculate_moon_position(jd)
    elif planet_name == "Rahu":
        tropical_longitude = calculate_rahu_position(jd)
    elif planet_name == "Ketu":
        rahu_lon = calculate_rahu_position(jd)
        tropical_longitude = normalize_angle(rahu_lon + 180.0)
    else:
        tropical_longitude, _ = calculate_planet_position(jd, planet_name)
    
    sidereal_longitude = normalize_angle(tropical_longitude - ayanamsa)
    details = get_sign_star_sub(sidereal_longitude)
    
    return {
        "name": planet_name,
        "longitude": round(sidereal_longitude, 6),
        "longitude_dms": details["longitude_dms"],
        "sign": details["sign"]["name"],
        "sign_lord": details["sign"]["lord"],
        "star": details["star"]["name"],
        "star_lord": details["star"]["lord"],
        "sub_lord": details["sub_lord"],
        "sub_sub_lord": details.get("sub_sub_lord", "")
    }
