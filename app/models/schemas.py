"""
Pydantic Models for KP Astrology API

Defines request and response schemas for the API endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class LocationInfo(BaseModel):
    """Location information from Sri Lanka database."""
    key: str
    name: str
    latitude: float
    longitude: float


class CalculationRequest(BaseModel):
    """
    Request model for KP calculations.
    
    Supports either direct coordinates or Sri Lanka location selection.
    """
    date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    time: str = Field(..., description="Birth time in HH:MM format (24-hour)")
    latitude: Optional[float] = Field(None, description="Latitude in decimal degrees (positive for North)")
    longitude: Optional[float] = Field(None, description="Longitude in decimal degrees (positive for East)")
    timezone: Optional[float] = Field(5.5, description="Timezone offset from UTC (default: 5.5 for Sri Lanka)")
    location: Optional[str] = Field(None, description="Sri Lanka location key (e.g., 'colombo', 'galle')")
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format."""
        try:
            parts = v.split('-')
            if len(parts) != 3:
                raise ValueError()
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 1 or month < 1 or month > 12 or day < 1 or day > 31:
                raise ValueError()
            return v
        except:
            raise ValueError("Date must be in YYYY-MM-DD format")
    
    @field_validator('time')
    @classmethod
    def validate_time(cls, v):
        """Validate time format."""
        try:
            parts = v.split(':')
            if len(parts) < 2:
                raise ValueError()
            hour, minute = int(parts[0]), int(parts[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
            return v
        except:
            raise ValueError("Time must be in HH:MM format (24-hour)")


class SignInfo(BaseModel):
    """Sign (Rashi) information."""
    name: str
    lord: str
    position: float = Field(..., description="Position within sign in degrees")


class StarInfo(BaseModel):
    """Star (Nakshatra) information."""
    name: str
    lord: str
    pada: int = Field(..., ge=1, le=4, description="Pada/quarter (1-4)")


class PlanetPosition(BaseModel):
    """Complete planetary position with KP details."""
    name: str
    longitude: float = Field(..., description="Sidereal longitude (0-360)")
    longitude_dms: str = Field(..., description="Longitude in degrees-minutes-seconds format")
    sign: str
    sign_lord: str
    star: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: Optional[str] = ""
    pada: int
    retrograde: bool = False


class HouseCusp(BaseModel):
    """House cusp (Bhawa) with KP details."""
    house: int = Field(..., ge=1, le=12, description="House number (1-12)")
    bhawa: int = Field(..., ge=1, le=12, description="Bhawa number (same as house)")
    longitude: float = Field(..., description="Sidereal longitude of cusp")
    longitude_dms: str = Field(..., description="Longitude in degrees-minutes-seconds format")
    sign: str
    sign_lord: str
    star: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: Optional[str] = ""
    pada: int


class AscendantInfo(BaseModel):
    """Ascendant (Lagna) information."""
    longitude: float
    longitude_dms: str
    sign: str
    sign_lord: str
    star: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: Optional[str] = ""


class AyanamsaInfo(BaseModel):
    """Ayanamsa calculation details."""
    value: float = Field(..., description="Ayanamsa in decimal degrees")
    dms: str = Field(..., description="Ayanamsa in degrees-minutes-seconds")
    type: str = Field("KP New (Balachandran)", description="Ayanamsa type used")


class LocationUsed(BaseModel):
    """Location details used in calculation."""
    name: Optional[str] = None
    latitude: float
    longitude: float
    timezone: float


class CalculationResponse(BaseModel):
    """
    Complete KP calculation response.
    
    Contains all planetary positions, house cusps, and ayanamsa details.
    """
    success: bool = True
    date: str
    time: str
    location: LocationUsed
    julian_day: float
    ayanamsa: AyanamsaInfo
    ascendant: AscendantInfo
    planets: List[PlanetPosition]
    houses: List[HouseCusp]
    house_system: str = "Placidus"


class LocationListResponse(BaseModel):
    """Response for listing available Sri Lanka locations."""
    success: bool = True
    count: int
    locations: List[LocationInfo]


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None
