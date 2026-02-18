"""
API Routes for KP Astrology System

Provides REST endpoints for:
- /calculate - Main KP calculation endpoint (with Vimshottari Dasha)
- /calculate-horary - KP Horary chart endpoint (1-249 system)
- /locations - List available Sri Lanka locations
- /health - Health check endpoint
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

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
    LocationInfo,
    HoraryRequest,
    HoraryResponse,
    HoraryInfo,
    DashaInfo,
    DashaPeriod,
    MahadashaInfo,
    AntardashaInfo,
    CurrentDashaInfo
)
from app.core.kp_data import get_location, list_locations, SRI_LANKA_LOCATIONS
from app.services.astronomy import date_to_julian_day, format_degrees_dms
from app.services.ayanamsa import calculate_kp_new_ayanamsa, calculate_ayanamsa
from app.services.planets import calculate_planet_positions
from app.services.houses import calculate_house_cusps, calculate_ascendant, rotate_house_cusps
from app.services.dasha import get_full_dasha_info
from app.services.horary import get_horary_info, generate_horary_table


router = APIRouter()


@router.post("/calculate", response_model=CalculationResponse, tags=["🔮 Chart Calculations"])
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
        
        # Calculate Ayanamsa (supports old, new, or manual)
        ayanamsa, ayanamsa_type_label = calculate_ayanamsa(
            jd, 
            request.ayanamsa_type or "new",
            request.manual_ayanamsa
        )
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
                type=ayanamsa_type_label
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
        
        # Add Vimshottari Dasha information
        # Find Moon's longitude for Dasha calculation
        moon_longitude = None
        for planet in planets:
            if planet["name"] == "Moon":
                moon_longitude = planet["longitude"]
                break
        
        if moon_longitude is not None:
            try:
                birth_datetime = datetime(
                    year, month, day, hour, minute, 0
                )
                dasha_data = get_full_dasha_info(moon_longitude, birth_datetime)
                
                # Build response dict with dasha
                response_dict = response.model_dump()
                response_dict["dasha"] = {
                    "birth_dasha_lord": dasha_data["birth_dasha_lord"],
                    "birth_dasha_balance_years": dasha_data["birth_dasha_balance_years"],
                    "birth_nakshatra": dasha_data["birth_nakshatra"],
                    "mahadasha_periods": dasha_data["mahadasha_periods"],
                    "current_dasha": dasha_data.get("current_dasha")
                }
                return response_dict
            except Exception as dasha_error:
                # Log error but continue without dasha
                import logging
                logging.warning(f"Dasha calculation error: {dasha_error}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/locations", response_model=LocationListResponse, tags=["📍 Locations"])
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


@router.get("/locations/{location_key}", tags=["📍 Locations"])
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


@router.get("/health", tags=["🔧 Utilities"])
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


@router.get("/ayanamsa", tags=["🔧 Utilities"])
async def get_ayanamsa(
    date: str, 
    time: str = "12:00", 
    timezone: float = 5.5,
    ayanamsa_type: str = "new",
    manual_ayanamsa: float = None
):
    """
    Get ayanamsa for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (default: 12:00)
        timezone: Timezone offset (default: 5.5)
        ayanamsa_type: 'old' (KSK), 'new' (Balachandran), or 'manual'
        manual_ayanamsa: Custom value when type='manual'
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
        ayanamsa, type_label = calculate_ayanamsa(jd, ayanamsa_type, manual_ayanamsa)
        
        return {
            "success": True,
            "date": date,
            "time": time,
            "julian_day": round(jd, 6),
            "ayanamsa": {
                "decimal": round(ayanamsa, 6),
                "dms": format_degrees_dms(ayanamsa),
                "type": type_label
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculate-horary", response_model=HoraryResponse, tags=["🎯 Horary Astrology"])
async def calculate_horary_endpoint(request: HoraryRequest):
    """
    Calculate KP Horary chart based on number (1-249).
    
    The KP Horary system uses the horary number ONLY to determine the
    Ascendant (Lagna). All planetary positions and house cusps are
    calculated for the time of judgment (when the question is asked).
    
    If time is not provided, the server's current time (converted to the
    location's timezone) is used automatically.
    
    Example request (auto time):
    ```json
    {
        "horary_number": 56,
        "date": "2026-02-18",
        "location": "colombo"
    }
    ```
    
    Example request (manual time):
    ```json
    {
        "horary_number": 56,
        "date": "2026-02-18",
        "time": "21:15",
        "location": "colombo"
    }
    ```
    """
    try:
        # Resolve location
        if request.location:
            try:
                loc_data = get_location(request.location)
                latitude = loc_data["latitude"]
                longitude_geo = loc_data["longitude"]
                timezone = loc_data["timezone"]
                location_name = loc_data["name"]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        elif request.latitude is not None and request.longitude is not None:
            latitude = request.latitude
            longitude_geo = request.longitude
            timezone = request.timezone if request.timezone is not None else 5.5
            location_name = None
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'location' or both 'latitude' and 'longitude' must be provided"
            )
        
        # Parse date
        date_parts = request.date.split("-")
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        
        # Determine time of judgment
        # If time is not provided, use server's current time in the location's timezone
        if request.time:
            time_parts = request.time.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            second = 0
        else:
            from datetime import timedelta
            # Get current UTC time, then offset by the location's timezone
            now_utc = datetime.utcnow()
            local_time = now_utc + timedelta(hours=timezone)
            hour = local_time.hour
            minute = local_time.minute
            second = local_time.second
        
        judgment_time_str = f"{hour:02d}:{minute:02d}"
        
        # Calculate Julian Day for the time of judgment
        jd = date_to_julian_day(year, month, day, hour, minute, second, timezone)
        
        # Calculate Ayanamsa (supports old, new, or manual)
        ayanamsa, ayanamsa_type_label = calculate_ayanamsa(
            jd,
            request.ayanamsa_type or "new",
            request.manual_ayanamsa
        )
        ayanamsa_dms = format_degrees_dms(ayanamsa)
        
        # Calculate planetary positions at the time of judgment
        planets = calculate_planet_positions(jd, ayanamsa)
        
        # Calculate house cusps at the time of judgment
        houses = calculate_house_cusps(jd, latitude, longitude_geo, ayanamsa)
        
        # =====================================================================
        # HORARY ASCENDANT & HOUSE CUSP ROTATION
        # In KP Horary, the Ascendant is determined by the horary number.
        # All 12 house cusps must be rotated by the offset between the
        # horary Ascendant and the astronomical Ascendant, so that house 1
        # starts at the horary degree. Sign/Star/Sub are re-calculated
        # for each rotated cusp.
        # =====================================================================
        horary_info = get_horary_info(request.horary_number)
        horary_asc_longitude = horary_info["start_longitude"]
        
        # Get the astronomical sidereal Ascendant at judgment time
        astronomical_asc = calculate_ascendant(jd, latitude, longitude_geo, ayanamsa)
        astronomical_asc_longitude = astronomical_asc["longitude"]
        
        # Compute rotation offset and rotate all 12 house cusps
        rotation_offset = horary_asc_longitude - astronomical_asc_longitude
        houses = rotate_house_cusps(houses, rotation_offset)
        
        # Build horary Ascendant details from the horary number
        from app.services.sublord import get_sign_star_sub
        horary_asc_details = get_sign_star_sub(horary_asc_longitude)
        
        ascendant_data = {
            "longitude": round(horary_asc_longitude, 6),
            "longitude_dms": horary_asc_details["longitude_dms"],
            "sign": horary_asc_details["sign"]["name"],
            "sign_lord": horary_asc_details["sign"]["lord"],
            "star": horary_asc_details["star"]["name"],
            "star_lord": horary_asc_details["star"]["lord"],
            "sub_lord": horary_asc_details["sub_lord"],
            "sub_sub_lord": horary_asc_details.get("sub_sub_lord", "")
        }
        
        # Build response
        response = HoraryResponse(
            success=True,
            horary=HoraryInfo(
                number=request.horary_number,
                target_ascendant=horary_asc_longitude,
                target_ascendant_dms=format_degrees_dms(horary_asc_longitude),
                sign=horary_info["sign"],
                sign_lord=horary_info["sign_lord"],
                star=horary_info["nakshatra"],
                star_lord=horary_info["star_lord"],
                sub_lord=horary_info["sub_lord"]
            ),
            time=judgment_time_str,
            date=request.date,
            location=LocationUsed(
                name=location_name,
                latitude=latitude,
                longitude=longitude_geo,
                timezone=timezone
            ),
            julian_day=round(jd, 6),
            ayanamsa=AyanamsaInfo(
                value=round(ayanamsa, 6),
                dms=ayanamsa_dms,
                type=ayanamsa_type_label
            ),
            ascendant=AscendantInfo(
                longitude=ascendant_data["longitude"],
                longitude_dms=ascendant_data["longitude_dms"],
                sign=ascendant_data["sign"],
                sign_lord=ascendant_data["sign_lord"],
                star=ascendant_data["star"],
                star_lord=ascendant_data["star_lord"],
                sub_lord=ascendant_data["sub_lord"],
                sub_sub_lord=ascendant_data.get("sub_sub_lord", "")
            ),
            planets=[PlanetPosition(**p) for p in planets],
            houses=[HouseCusp(**h) for h in houses],
            house_system="Placidus"
        )
        
        # Add Vimshottari Dasha information
        # Find Moon's longitude for Dasha calculation
        moon_longitude = None
        for planet in planets:
            if planet["name"] == "Moon":
                moon_longitude = planet["longitude"]
                break
        
        if moon_longitude is not None:
            try:
                judgment_datetime = datetime(year, month, day, hour, minute, second)
                dasha_data = get_full_dasha_info(moon_longitude, judgment_datetime)
                
                response_dict = response.model_dump()
                response_dict["dasha"] = {
                    "birth_dasha_lord": dasha_data["birth_dasha_lord"],
                    "birth_dasha_balance_years": dasha_data["birth_dasha_balance_years"],
                    "birth_nakshatra": dasha_data["birth_nakshatra"],
                    "mahadasha_periods": dasha_data["mahadasha_periods"],
                    "current_dasha": dasha_data.get("current_dasha")
                }
                return response_dict
            except Exception as dasha_error:
                import logging
                logging.warning(f"Horary Dasha calculation error: {dasha_error}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Horary calculation error: {str(e)}")


@router.get("/horary-table", tags=["🎯 Horary Astrology"])
async def get_horary_table_endpoint():
    """
    Get the complete KP Horary number table (1-249).
    
    Returns the mapping of each horary number to its zodiac position
    and Sign-Star-Sub combination.
    
    This is useful for reference and verification.
    """
    try:
        # Generate table if not already cached
        generate_horary_table()
        
        table_data = []
        for num in range(1, 250):
            info = get_horary_info(num)
            table_data.append({
                "number": num,
                "start_longitude": round(info["start_longitude"], 6),
                "longitude_dms": format_degrees_dms(info["start_longitude"]),
                "sign": info["sign"],
                "sign_lord": info["sign_lord"],
                "nakshatra": info["nakshatra"],
                "star_lord": info["star_lord"],
                "sub_lord": info["sub_lord"]
            })
        
        return {
            "success": True,
            "count": 249,
            "table": table_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating horary table: {str(e)}")

