"""
API Routes for KP Astrology System

Provides REST endpoints for:
- /calculate - Main KP calculation endpoint
- /locations - List available Sri Lanka locations
- /health - Health check endpoint
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models.schemas import (
    CalculationRequest,
    CalculationResponse,
    LocationListResponse,
    ErrorResponse,
    PlanetPosition,
    HouseCusp,
    AyanamsaInfo,
    AscendantInfo,
    LocationUsed,
    LocationInfo
)
from app.core.kp_data import get_location, list_locations, SRI_LANKA_LOCATIONS
from app.services.astronomy import date_to_julian_day, format_degrees_dms
from app.services.ayanamsa import calculate_kp_new_ayanamsa
from app.services.planets import calculate_planet_positions
from app.services.houses import calculate_house_cusps, calculate_ascendant


router = APIRouter()


@router.post("/calculate", response_model=CalculationResponse)
async def calculate_chart(request: CalculationRequest):
    """
    Calculate complete KP astrology chart.
    
    This endpoint calculates:
    - Planetary positions with Sign/Star/Sub lords
    - House cusps (Bhawa) with Sign/Star/Sub lords
    - Ascendant details
    - KP New Ayanamsa
    
    Either provide latitude/longitude directly, or use the 'location'
    parameter to select a Sri Lanka location.
    
    Example request with location:
    ```json
    {
        "date": "2002-04-21",
        "time": "08:09",
        "location": "galle"
    }
    ```
    
    Example with coordinates:
    ```json
    {
        "date": "2002-04-21",
        "time": "08:09",
        "latitude": 6.0535,
        "longitude": 80.2210,
        "timezone": 5.5
    }
    ```
    """
    try:
        # Resolve location
        if request.location:
            # Use Sri Lanka location database
            try:
                loc_data = get_location(request.location)
                latitude = loc_data["latitude"]
                longitude = loc_data["longitude"]
                timezone = loc_data["timezone"]
                location_name = loc_data["name"]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        elif request.latitude is not None and request.longitude is not None:
            # Use provided coordinates
            latitude = request.latitude
            longitude = request.longitude
            timezone = request.timezone if request.timezone is not None else 5.5
            location_name = None
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'location' or both 'latitude' and 'longitude' must be provided"
            )
        
        # Parse date and time
        date_parts = request.date.split("-")
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        
        time_parts = request.time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        # Calculate Julian Day
        jd = date_to_julian_day(year, month, day, hour, minute, 0.0, timezone)
        
        # Calculate KP New Ayanamsa
        ayanamsa = calculate_kp_new_ayanamsa(jd)
        ayanamsa_dms = format_degrees_dms(ayanamsa)
        
        # Calculate planetary positions
        planets = calculate_planet_positions(jd, ayanamsa)
        
        # Calculate house cusps
        houses = calculate_house_cusps(jd, latitude, longitude, ayanamsa)
        
        # Calculate Ascendant
        ascendant = calculate_ascendant(jd, latitude, longitude, ayanamsa)
        
        # Build response
        response = CalculationResponse(
            success=True,
            date=request.date,
            time=request.time,
            location=LocationUsed(
                name=location_name,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone
            ),
            julian_day=round(jd, 6),
            ayanamsa=AyanamsaInfo(
                value=round(ayanamsa, 6),
                dms=ayanamsa_dms,
                type="KP New (Balachandran)"
            ),
            ascendant=AscendantInfo(
                longitude=ascendant["longitude"],
                longitude_dms=ascendant["longitude_dms"],
                sign=ascendant["sign"],
                sign_lord=ascendant["sign_lord"],
                star=ascendant["star"],
                star_lord=ascendant["star_lord"],
                sub_lord=ascendant["sub_lord"],
                sub_sub_lord=ascendant.get("sub_sub_lord", "")
            ),
            planets=[PlanetPosition(**p) for p in planets],
            houses=[HouseCusp(**h) for h in houses],
            house_system="Placidus"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/locations", response_model=LocationListResponse)
async def get_locations():
    """
    Get list of available Sri Lanka locations.
    
    Returns all pre-configured locations with their coordinates.
    Use the 'key' value in the /calculate endpoint's 'location' field.
    """
    locations = list_locations()
    
    return LocationListResponse(
        success=True,
        count=len(locations),
        locations=[LocationInfo(**loc) for loc in locations]
    )


@router.get("/locations/{location_key}")
async def get_single_location(location_key: str):
    """
    Get details for a specific Sri Lanka location.
    
    Args:
        location_key: Location identifier (e.g., 'colombo', 'galle')
    """
    try:
        loc_data = get_location(location_key)
        return {
            "success": True,
            "location": LocationInfo(
                key=location_key.lower().replace(" ", "_"),
                name=loc_data["name"],
                latitude=loc_data["latitude"],
                longitude=loc_data["longitude"]
            )
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns status of the API.
    """
    return {
        "status": "healthy",
        "service": "KP Astrology API",
        "version": "1.0.0"
    }


@router.get("/ayanamsa")
async def get_ayanamsa(date: str, time: str = "12:00", timezone: float = 5.5):
    """
    Get KP New Ayanamsa for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (default: 12:00)
        timezone: Timezone offset (default: 5.5)
    """
    try:
        # Parse date
        date_parts = date.split("-")
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        
        # Parse time
        time_parts = time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        # Calculate
        jd = date_to_julian_day(year, month, day, hour, minute, 0.0, timezone)
        ayanamsa = calculate_kp_new_ayanamsa(jd)
        
        return {
            "success": True,
            "date": date,
            "time": time,
            "julian_day": round(jd, 6),
            "ayanamsa": {
                "decimal": round(ayanamsa, 6),
                "dms": format_degrees_dms(ayanamsa),
                "type": "KP New (Balachandran)"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
