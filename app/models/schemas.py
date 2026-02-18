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
    ayanamsa_type: Optional[str] = Field("new", description="Ayanamsa type: 'old' (KSK), 'new' (Balachandran), or 'manual'")
    manual_ayanamsa: Optional[float] = Field(None, description="Custom ayanamsa value in degrees (required when ayanamsa_type='manual')")
    
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
    dasha: Optional[dict] = None  # Vimshottari Dasha information


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


# =============================================================================
# HORARY MODELS
# =============================================================================

class HoraryRequest(BaseModel):
    """
    Request model for KP Horary calculations.
    
    The horary number (1-249) determines the Ascendant (Lagna) degree.
    Planetary positions and house cusps are calculated for the time of judgment.
    If time is not provided, server's current time (in the location's timezone) is used.
    """
    horary_number: int = Field(..., ge=1, le=249, description="KP Horary number (1-249)")
    date: str = Field(..., description="Date of query in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Time of judgment in HH:MM format (24-hour). If not provided, server current time is used.")
    latitude: Optional[float] = Field(None, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(None, description="Longitude in decimal degrees")
    timezone: Optional[float] = Field(5.5, description="Timezone offset from UTC")
    location: Optional[str] = Field(None, description="Sri Lanka location key")
    ayanamsa_type: Optional[str] = Field("new", description="Ayanamsa type: 'old' (KSK), 'new' (Balachandran), or 'manual'")
    manual_ayanamsa: Optional[float] = Field(None, description="Custom ayanamsa value in degrees (required when ayanamsa_type='manual')")
    
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


class HoraryInfo(BaseModel):
    """Horary number details."""
    number: int
    target_ascendant: float = Field(..., description="Target Ascendant degree")
    target_ascendant_dms: str = Field(..., description="Target Ascendant in DMS format")
    sign: str
    sign_lord: str
    star: str
    star_lord: str
    sub_lord: str


class HoraryResponse(BaseModel):
    """
    Response model for KP Horary calculations.
    
    Contains the horary details plus full chart like CalculationResponse.
    Ascendant is determined by horary number; planets/houses by time of judgment.
    """
    success: bool = True
    horary: HoraryInfo
    time: str = Field(..., description="Time of judgment used (HH:MM)")
    date: str
    location: LocationUsed
    julian_day: float
    ayanamsa: AyanamsaInfo
    ascendant: AscendantInfo
    planets: List[PlanetPosition]
    houses: List[HouseCusp]
    house_system: str = "Placidus"
    dasha: Optional[dict] = None


# =============================================================================
# DASHA MODELS
# =============================================================================

class DashaPeriod(BaseModel):
    """A single Dasha period (Mahadasha or Antardasha)."""
    planet: str
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    duration_years: float = Field(..., description="Duration in years")


class AntardashaInfo(BaseModel):
    """Antardasha (sub-period) within a Mahadasha."""
    planet: str
    start_date: str
    end_date: str
    duration_years: float


class MahadashaInfo(BaseModel):
    """Mahadasha (major period) with its Antardashas."""
    planet: str
    start_date: str
    end_date: str
    duration_years: float
    antardasha: List[AntardashaInfo]


class CurrentDashaInfo(BaseModel):
    """Currently running Dasha periods."""
    mahadasha: DashaPeriod
    antardasha: Optional[DashaPeriod] = None
    pratyantardasha: Optional[DashaPeriod] = None
    sookshma_dasha: Optional[DashaPeriod] = None
    dasha_string: str = Field(..., description="Formatted string like 'Jupiter-Saturn-Mercury-Venus'")


class DashaInfo(BaseModel):
    """Complete Vimshottari Dasha information."""
    birth_dasha_lord: str = Field(..., description="Planet ruling Dasha at birth")
    birth_dasha_balance_years: float = Field(..., description="Years remaining of birth Dasha")
    birth_nakshatra: str = Field(..., description="Moon's Nakshatra at birth")
    mahadasha_periods: List[MahadashaInfo]
    current_dasha: Optional[CurrentDashaInfo] = None

