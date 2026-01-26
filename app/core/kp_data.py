"""
KP Astrology Static Data Module

Contains all static data for KP calculations:
- Vimshottari Dasha periods and order
- 27 Nakshatras with degree ranges and rulers
- 12 Zodiac signs with rulers
- Sri Lanka locations database
"""

# =============================================================================
# VIMSHOTTARI DASHA SYSTEM
# =============================================================================

# Dasha order: Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# Dasha periods in years (total = 120 years)
VIMSHOTTARI_PERIODS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17
}

# Total dasha period
TOTAL_DASHA_YEARS = 120

# Nakshatra span in degrees (13°20' = 13.333... degrees)
NAKSHATRA_SPAN = 13.0 + 20.0 / 60.0  # 13.333333...

# =============================================================================
# 27 NAKSHATRAS WITH RULERS
# =============================================================================

NAKSHATRAS = [
    {"index": 1, "name": "Ashwini", "lord": "Ketu", "start": 0.0},
    {"index": 2, "name": "Bharani", "lord": "Venus", "start": 13.333333},
    {"index": 3, "name": "Krittika", "lord": "Sun", "start": 26.666667},
    {"index": 4, "name": "Rohini", "lord": "Moon", "start": 40.0},
    {"index": 5, "name": "Mrigashira", "lord": "Mars", "start": 53.333333},
    {"index": 6, "name": "Ardra", "lord": "Rahu", "start": 66.666667},
    {"index": 7, "name": "Punarvasu", "lord": "Jupiter", "start": 80.0},
    {"index": 8, "name": "Pushya", "lord": "Saturn", "start": 93.333333},
    {"index": 9, "name": "Ashlesha", "lord": "Mercury", "start": 106.666667},
    {"index": 10, "name": "Magha", "lord": "Ketu", "start": 120.0},
    {"index": 11, "name": "Purva Phalguni", "lord": "Venus", "start": 133.333333},
    {"index": 12, "name": "Uttara Phalguni", "lord": "Sun", "start": 146.666667},
    {"index": 13, "name": "Hasta", "lord": "Moon", "start": 160.0},
    {"index": 14, "name": "Chitra", "lord": "Mars", "start": 173.333333},
    {"index": 15, "name": "Swati", "lord": "Rahu", "start": 186.666667},
    {"index": 16, "name": "Vishakha", "lord": "Jupiter", "start": 200.0},
    {"index": 17, "name": "Anuradha", "lord": "Saturn", "start": 213.333333},
    {"index": 18, "name": "Jyeshtha", "lord": "Mercury", "start": 226.666667},
    {"index": 19, "name": "Mula", "lord": "Ketu", "start": 240.0},
    {"index": 20, "name": "Purva Ashadha", "lord": "Venus", "start": 253.333333},
    {"index": 21, "name": "Uttara Ashadha", "lord": "Sun", "start": 266.666667},
    {"index": 22, "name": "Shravana", "lord": "Moon", "start": 280.0},
    {"index": 23, "name": "Dhanishta", "lord": "Mars", "start": 293.333333},
    {"index": 24, "name": "Shatabhisha", "lord": "Rahu", "start": 306.666667},
    {"index": 25, "name": "Purva Bhadrapada", "lord": "Jupiter", "start": 320.0},
    {"index": 26, "name": "Uttara Bhadrapada", "lord": "Saturn", "start": 333.333333},
    {"index": 27, "name": "Revati", "lord": "Mercury", "start": 346.666667},
]

# =============================================================================
# 12 ZODIAC SIGNS WITH LORDS (Traditional Vedic/KP)
# =============================================================================

ZODIAC_SIGNS = [
    {"index": 1, "name": "Aries", "lord": "Mars", "start": 0.0, "end": 30.0},
    {"index": 2, "name": "Taurus", "lord": "Venus", "start": 30.0, "end": 60.0},
    {"index": 3, "name": "Gemini", "lord": "Mercury", "start": 60.0, "end": 90.0},
    {"index": 4, "name": "Cancer", "lord": "Moon", "start": 90.0, "end": 120.0},
    {"index": 5, "name": "Leo", "lord": "Sun", "start": 120.0, "end": 150.0},
    {"index": 6, "name": "Virgo", "lord": "Mercury", "start": 150.0, "end": 180.0},
    {"index": 7, "name": "Libra", "lord": "Venus", "start": 180.0, "end": 210.0},
    {"index": 8, "name": "Scorpio", "lord": "Mars", "start": 210.0, "end": 240.0},
    {"index": 9, "name": "Sagittarius", "lord": "Jupiter", "start": 240.0, "end": 270.0},
    {"index": 10, "name": "Capricorn", "lord": "Saturn", "start": 270.0, "end": 300.0},
    {"index": 11, "name": "Aquarius", "lord": "Saturn", "start": 300.0, "end": 330.0},
    {"index": 12, "name": "Pisces", "lord": "Jupiter", "start": 330.0, "end": 360.0},
]

# =============================================================================
# PLANETS FOR CALCULATIONS
# =============================================================================

# Swiss Ephemeris planet codes
PLANETS = {
    "Sun": 0,
    "Moon": 1,
    "Mars": 4,
    "Mercury": 2,
    "Jupiter": 5,
    "Venus": 3,
    "Saturn": 6,
    "Rahu": 10,  # Mean Node (True Node is 11)
}

# Planet display order
PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# =============================================================================
# SRI LANKA LOCATIONS DATABASE
# =============================================================================

SRI_LANKA_LOCATIONS = {
    "colombo": {
        "name": "Colombo",
        "latitude": 6.9271,
        "longitude": 79.8612,
        "timezone": 5.5
    },
    "galle": {
        "name": "Galle",
        "latitude": 6.0535,
        "longitude": 80.2210,
        "timezone": 5.5
    },
    "kandy": {
        "name": "Kandy",
        "latitude": 7.2906,
        "longitude": 80.6337,
        "timezone": 5.5
    },
    "jaffna": {
        "name": "Jaffna",
        "latitude": 9.6615,
        "longitude": 80.0255,
        "timezone": 5.5
    },
    "trincomalee": {
        "name": "Trincomalee",
        "latitude": 8.5874,
        "longitude": 81.2152,
        "timezone": 5.5
    },
    "batticaloa": {
        "name": "Batticaloa",
        "latitude": 7.7310,
        "longitude": 81.6747,
        "timezone": 5.5
    },
    "negombo": {
        "name": "Negombo",
        "latitude": 7.2008,
        "longitude": 79.8358,
        "timezone": 5.5
    },
    "anuradhapura": {
        "name": "Anuradhapura",
        "latitude": 8.3114,
        "longitude": 80.4037,
        "timezone": 5.5
    },
    "polonnaruwa": {
        "name": "Polonnaruwa",
        "latitude": 7.9403,
        "longitude": 81.0188,
        "timezone": 5.5
    },
    "matara": {
        "name": "Matara",
        "latitude": 5.9549,
        "longitude": 80.5550,
        "timezone": 5.5
    },
    "kurunegala": {
        "name": "Kurunegala",
        "latitude": 7.4867,
        "longitude": 80.3647,
        "timezone": 5.5
    },
    "ratnapura": {
        "name": "Ratnapura",
        "latitude": 6.7056,
        "longitude": 80.3847,
        "timezone": 5.5
    },
    "badulla": {
        "name": "Badulla",
        "latitude": 6.9934,
        "longitude": 81.0550,
        "timezone": 5.5
    },
    "nuwara_eliya": {
        "name": "Nuwara Eliya",
        "latitude": 6.9497,
        "longitude": 80.7891,
        "timezone": 5.5
    },
    "hambantota": {
        "name": "Hambantota",
        "latitude": 6.1241,
        "longitude": 81.1185,
        "timezone": 5.5
    },
    "vavuniya": {
        "name": "Vavuniya",
        "latitude": 8.7542,
        "longitude": 80.4982,
        "timezone": 5.5
    },
    "ampara": {
        "name": "Ampara",
        "latitude": 7.2976,
        "longitude": 81.6720,
        "timezone": 5.5
    },
    "kegalle": {
        "name": "Kegalle",
        "latitude": 7.2523,
        "longitude": 80.3456,
        "timezone": 5.5
    },
    "mannar": {
        "name": "Mannar",
        "latitude": 8.9810,
        "longitude": 79.9044,
        "timezone": 5.5
    },
    "kalutara": {
        "name": "Kalutara",
        "latitude": 6.5854,
        "longitude": 79.9607,
        "timezone": 5.5
    },
    "puttalam": {
        "name": "Puttalam",
        "latitude": 8.0362,
        "longitude": 79.8283,
        "timezone": 5.5
    },
    "chilaw": {
        "name": "Chilaw",
        "latitude": 7.5758,
        "longitude": 79.7953,
        "timezone": 5.5
    },
    "matale": {
        "name": "Matale",
        "latitude": 7.4675,
        "longitude": 80.6234,
        "timezone": 5.5
    },
    "kilinochchi": {
        "name": "Kilinochchi",
        "latitude": 9.3803,
        "longitude": 80.3770,
        "timezone": 5.5
    },
    "mullaitivu": {
        "name": "Mullaitivu",
        "latitude": 9.2671,
        "longitude": 80.8142,
        "timezone": 5.5
    }
}


def get_location(location_key: str) -> dict:
    """
    Get location data by key (case-insensitive).
    
    Args:
        location_key: Location identifier (e.g., 'colombo', 'galle')
        
    Returns:
        Location dict with name, latitude, longitude, timezone
        
    Raises:
        ValueError: If location not found
    """
    key = location_key.lower().replace(" ", "_")
    if key not in SRI_LANKA_LOCATIONS:
        available = ", ".join(sorted(SRI_LANKA_LOCATIONS.keys()))
        raise ValueError(f"Location '{location_key}' not found. Available: {available}")
    return SRI_LANKA_LOCATIONS[key]


def list_locations() -> list:
    """Return list of all available Sri Lanka locations."""
    return [
        {
            "key": key,
            "name": loc["name"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"]
        }
        for key, loc in sorted(SRI_LANKA_LOCATIONS.items())
    ]
