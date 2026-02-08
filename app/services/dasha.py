"""
Vimshottari Dasha Calculation Module

This module implements the Vimshottari Dasha system used in KP Astrology.
The Vimshottari Dasha is a 120-year planetary period system based on
the Moon's position in the Nakshatra at birth.

Key Concepts:
- Mahadasha: Major planetary period (6-20 years depending on planet)
- Antardasha (Bhukti): Sub-period within Mahadasha
- Pratyantardasha: Sub-sub period within Antardasha

The sequence of planets follows the Nakshatra lords:
Ketu -> Venus -> Sun -> Moon -> Mars -> Rahu -> Jupiter -> Saturn -> Mercury

Author: KP Astrology Backend
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.core.kp_data import (
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_PERIODS,
    NAKSHATRAS
)
from app.services.sublord import NAKSHATRA_SPAN, TOTAL_DASHA_YEARS


@dataclass
class DashaPeriod:
    """Represents a single Dasha period."""
    planet: str
    start_date: datetime
    end_date: datetime
    duration_years: float
    duration_days: int


# =============================================================================
# DASHA BALANCE CALCULATION
# =============================================================================

def calculate_dasha_balance(moon_longitude: float, birth_datetime: datetime) -> Dict:
    """
    Calculate the Dasha balance at birth based on Moon's position.
    
    The Moon's position in its Nakshatra determines:
    1. Which Dasha is running at birth
    2. How much of that Dasha remains (balance)
    
    Formula:
    balance_ratio = (nakshatra_end - moon_position) / nakshatra_span
    balance_years = balance_ratio * planet_dasha_period
    
    Args:
        moon_longitude: Moon's sidereal longitude (0-360)
        birth_datetime: Birth date and time
        
    Returns:
        Dict containing:
        - birth_dasha_lord: Planet whose Dasha is running at birth
        - balance_years: Remaining years of birth Dasha
        - balance_days: Remaining days of birth Dasha
        - dasha_start_date: When the birth Dasha started
        - dasha_end_date: When the birth Dasha ends
        - position_in_nakshatra: Moon's position within Nakshatra
        - nakshatra_name: Name of the Nakshatra
    """
    # Calculate which Nakshatra the Moon is in
    nakshatra_index = int(moon_longitude / NAKSHATRA_SPAN)
    if nakshatra_index >= 27:
        nakshatra_index = 0
    
    nakshatra = NAKSHATRAS[nakshatra_index]
    nakshatra_lord = nakshatra["lord"]
    nakshatra_start = nakshatra_index * NAKSHATRA_SPAN
    nakshatra_end = nakshatra_start + NAKSHATRA_SPAN
    
    # Position within the Nakshatra
    position_in_nakshatra = moon_longitude - nakshatra_start
    
    # Calculate balance ratio (how much of Nakshatra remains)
    # If Moon is at the start of Nakshatra, full Dasha remains
    # If Moon is at the end, almost no Dasha remains
    balance_ratio = (NAKSHATRA_SPAN - position_in_nakshatra) / NAKSHATRA_SPAN
    
    # Get the Dasha period for this planet
    dasha_lord = nakshatra_lord
    dasha_period_years = VIMSHOTTARI_PERIODS[dasha_lord]
    
    # Calculate balance
    balance_years = balance_ratio * dasha_period_years
    balance_days = int(balance_years * 365.25)
    
    # Calculate Dasha dates
    dasha_end_date = birth_datetime + timedelta(days=balance_days)
    elapsed_years = dasha_period_years - balance_years
    elapsed_days = int(elapsed_years * 365.25)
    dasha_start_date = birth_datetime - timedelta(days=elapsed_days)
    
    return {
        "birth_dasha_lord": dasha_lord,
        "balance_years": round(balance_years, 4),
        "balance_days": balance_days,
        "dasha_start_date": dasha_start_date,
        "dasha_end_date": dasha_end_date,
        "nakshatra_name": nakshatra["name"],
        "nakshatra_index": nakshatra_index + 1,  # 1-based index
        "position_in_nakshatra": round(position_in_nakshatra, 6)
    }


# =============================================================================
# MAHADASHA PERIODS
# =============================================================================

def calculate_mahadasha_periods(
    moon_longitude: float,
    birth_datetime: datetime,
    num_periods: int = 9
) -> List[DashaPeriod]:
    """
    Calculate Mahadasha periods from birth.
    
    Starting from the birth Dasha lord, generates the sequence of
    Mahadasha periods for the specified number of cycles.
    
    Args:
        moon_longitude: Moon's sidereal longitude
        birth_datetime: Birth date and time
        num_periods: Number of Mahadasha periods to calculate (default: 9 for one full cycle)
        
    Returns:
        List of DashaPeriod objects representing each Mahadasha
    """
    balance_info = calculate_dasha_balance(moon_longitude, birth_datetime)
    
    # Find starting index in Vimshottari order
    birth_dasha_lord = balance_info["birth_dasha_lord"]
    start_index = VIMSHOTTARI_ORDER.index(birth_dasha_lord)
    
    periods = []
    current_date = birth_datetime
    
    for i in range(num_periods):
        planet_index = (start_index + i) % 9
        planet = VIMSHOTTARI_ORDER[planet_index]
        
        if i == 0:
            # First Dasha uses balance
            duration_years = balance_info["balance_years"]
        else:
            duration_years = VIMSHOTTARI_PERIODS[planet]
        
        duration_days = int(duration_years * 365.25)
        end_date = current_date + timedelta(days=duration_days)
        
        periods.append(DashaPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            duration_years=round(duration_years, 4),
            duration_days=duration_days
        ))
        
        current_date = end_date
    
    return periods


# =============================================================================
# ANTARDASHA (BHUKTI) PERIODS
# =============================================================================

def calculate_antardasha_periods(mahadasha: DashaPeriod) -> List[DashaPeriod]:
    """
    Calculate Antardasha (sub-periods) within a Mahadasha.
    
    Each Mahadasha has 9 Antardashas in the Vimshottari sequence,
    starting from the Mahadasha lord itself.
    
    The duration of each Antardasha is proportional to:
    antardasha_years = (MD_years * AD_planet_period) / TOTAL_DASHA_YEARS
    
    Args:
        mahadasha: The Mahadasha period to subdivide
        
    Returns:
        List of DashaPeriod objects for each Antardasha
    """
    md_lord = mahadasha.planet
    md_duration_years = mahadasha.duration_years
    
    # Find starting index (Antardasha starts from Mahadasha lord)
    start_index = VIMSHOTTARI_ORDER.index(md_lord)
    
    periods = []
    current_date = mahadasha.start_date
    
    for i in range(9):
        planet_index = (start_index + i) % 9
        planet = VIMSHOTTARI_ORDER[planet_index]
        planet_period = VIMSHOTTARI_PERIODS[planet]
        
        # Antardasha duration formula
        ad_duration_years = (md_duration_years * planet_period) / TOTAL_DASHA_YEARS
        ad_duration_days = int(ad_duration_years * 365.25)
        
        end_date = current_date + timedelta(days=ad_duration_days)
        
        periods.append(DashaPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            duration_years=round(ad_duration_years, 4),
            duration_days=ad_duration_days
        ))
        
        current_date = end_date
    
    return periods


# =============================================================================
# PRATYANTARDASHA (SUB-SUB PERIODS)
# =============================================================================

def calculate_pratyantardasha_periods(antardasha: DashaPeriod) -> List[DashaPeriod]:
    """
    Calculate Pratyantardasha (sub-sub-periods) within an Antardasha.
    
    Similar logic to Antardasha, but divides the Antardasha period.
    Starts from the Antardasha lord.
    
    Args:
        antardasha: The Antardasha period to subdivide
        
    Returns:
        List of DashaPeriod objects for each Pratyantardasha
    """
    ad_lord = antardasha.planet
    ad_duration_years = antardasha.duration_years
    
    start_index = VIMSHOTTARI_ORDER.index(ad_lord)
    
    periods = []
    current_date = antardasha.start_date
    
    for i in range(9):
        planet_index = (start_index + i) % 9
        planet = VIMSHOTTARI_ORDER[planet_index]
        planet_period = VIMSHOTTARI_PERIODS[planet]
        
        # Pratyantardasha duration formula
        pad_duration_years = (ad_duration_years * planet_period) / TOTAL_DASHA_YEARS
        pad_duration_days = max(1, int(pad_duration_years * 365.25))  # At least 1 day
        
        end_date = current_date + timedelta(days=pad_duration_days)
        
        periods.append(DashaPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            duration_years=round(pad_duration_years, 4),
            duration_days=pad_duration_days
        ))
        
        current_date = end_date
    
    return periods


# =============================================================================
# SOOKSHMA DASHA (SUB-SUB-SUB PERIODS)
# =============================================================================

def calculate_sookshma_dasha_periods(pratyantardasha: DashaPeriod) -> List[DashaPeriod]:
    """
    Calculate Sookshma Dasha (sub-sub-sub-periods) within a Pratyantardasha.
    
    Level 4 in the Vimshottari hierarchy:
    Mahadasha -> Antardasha -> Pratyantardasha -> Sookshma Dasha
    
    Args:
        pratyantardasha: The Pratyantardasha period to subdivide
        
    Returns:
        List of DashaPeriod objects for each Sookshma Dasha
    """
    pad_lord = pratyantardasha.planet
    pad_duration_years = pratyantardasha.duration_years
    
    start_index = VIMSHOTTARI_ORDER.index(pad_lord)
    
    periods = []
    current_date = pratyantardasha.start_date
    
    for i in range(9):
        planet_index = (start_index + i) % 9
        planet = VIMSHOTTARI_ORDER[planet_index]
        planet_period = VIMSHOTTARI_PERIODS[planet]
        
        # Sookshma duration formula
        # Sookshma spans are very short (days)
        sd_duration_years = (pad_duration_years * planet_period) / TOTAL_DASHA_YEARS
        
        # Calculate precise days, hours for this level (as days might be fractional)
        total_days = sd_duration_years * 365.25
        duration_days = int(total_days)
        
        # Add a tiny buffer if duration is 0 due to int truncation (though usually > 0.5 days)
        if duration_days < 1:
            duration_days = 0 # Handled by timedelta, but logic keeps date continuous
            
        end_date = current_date + timedelta(days=total_days)
        
        periods.append(DashaPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            duration_years=round(sd_duration_years, 6),
            duration_days=duration_days
        ))
        
        current_date = end_date
    
    return periods


# =============================================================================
# CURRENT DASHA FINDER
# =============================================================================

def find_current_dasha(
    moon_longitude: float,
    birth_datetime: datetime,
    query_datetime: Optional[datetime] = None
) -> Dict:
    """
    Find the current running Dasha periods for a given date.
    
    Args:
        moon_longitude: Moon's sidereal longitude
        birth_datetime: Birth date and time
        query_datetime: Date to check (defaults to current date)
        
    Returns:
        Dict containing:
        - current_mahadasha: The current Mahadasha
        - current_antardasha: The current Antardasha
        - current_pratyantardasha: The current Pratyantardasha
        - current_sookshma_dasha: The current Sookshma Dasha (Level 4)
        - dasha_string: Formatted string like "Jupiter-Saturn-Mercury-Venus"
    """
    if query_datetime is None:
        query_datetime = datetime.now()
    
    # Get all Mahadashas (enough to cover typical lifespan)
    mahadashas = calculate_mahadasha_periods(
        moon_longitude, birth_datetime, num_periods=18  # 2 full cycles
    )
    
    current_md = None
    current_ad = None
    current_pad = None
    current_sd = None
    
    # Find current Mahadasha
    for md in mahadashas:
        if md.start_date <= query_datetime < md.end_date:
            current_md = md
            break
    
    if current_md is None:
        return {
            "current_mahadasha": None,
            "current_antardasha": None,
            "current_pratyantardasha": None,
            "current_sookshma_dasha": None,
            "dasha_string": "N/A",
            "error": "Query date is outside Dasha range"
        }
    
    # Find current Antardasha
    antardashas = calculate_antardasha_periods(current_md)
    for ad in antardashas:
        if ad.start_date <= query_datetime < ad.end_date:
            current_ad = ad
            break
    
    # Find current Pratyantardasha
    if current_ad:
        pratyantardashas = calculate_pratyantardasha_periods(current_ad)
        for pad in pratyantardashas:
            if pad.start_date <= query_datetime < pad.end_date:
                current_pad = pad
                break
    
    # Find current Sookshma Dasha (Level 4)
    if current_pad:
        sookshma_dashas = calculate_sookshma_dasha_periods(current_pad)
        for sd in sookshma_dashas:
            if sd.start_date <= query_datetime < sd.end_date:
                current_sd = sd
                break
    
    # Build dasha string
    parts = [current_md.planet]
    if current_ad:
        parts.append(current_ad.planet)
    if current_pad:
        parts.append(current_pad.planet)
    if current_sd:
        parts.append(current_sd.planet)
        
    dasha_string = "-".join(parts)
    
    return {
        "current_mahadasha": current_md,
        "current_antardasha": current_ad,
        "current_pratyantardasha": current_pad,
        "current_sookshma_dasha": current_sd,
        "dasha_string": dasha_string
    }


# =============================================================================
# FULL DASHA INFORMATION
# =============================================================================

def get_full_dasha_info(
    moon_longitude: float,
    birth_datetime: datetime,
    include_pratyantardasha: bool = False
) -> Dict:
    """
    Get complete Dasha information for a birth chart.
    
    This is the main entry point for Dasha calculations.
    
    Args:
        moon_longitude: Moon's sidereal longitude
        birth_datetime: Birth date and time
        include_pratyantardasha: Whether to include sub-sub periods
        
    Returns:
        Dict containing:
        - birth_dasha_lord: Planet ruling birth Dasha
        - birth_dasha_balance: Years remaining at birth
        - mahadasha_periods: List of all Mahadasha periods
        - current_dasha: Current running Dasha info
    """
    # Get birth Dasha balance
    balance_info = calculate_dasha_balance(moon_longitude, birth_datetime)
    
    # Get Mahadasha periods (one full cycle)
    mahadashas = calculate_mahadasha_periods(moon_longitude, birth_datetime, num_periods=9)
    
    # Get current Dasha
    current = find_current_dasha(moon_longitude, birth_datetime)
    
    # Format Mahadasha periods for API response
    formatted_periods = []
    for md in mahadashas:
        period_info = {
            "planet": md.planet,
            "start_date": md.start_date.strftime("%Y-%m-%d"),
            "end_date": md.end_date.strftime("%Y-%m-%d"),
            "duration_years": md.duration_years
        }
        
        # Optionally include Antardashas
        antardashas = calculate_antardasha_periods(md)
        period_info["antardasha"] = [
            {
                "planet": ad.planet,
                "start_date": ad.start_date.strftime("%Y-%m-%d"),
                "end_date": ad.end_date.strftime("%Y-%m-%d"),
                "duration_years": ad.duration_years
            }
            for ad in antardashas
        ]
        
        formatted_periods.append(period_info)
    
    # Format current Dasha
    current_dasha_info = None
    if current.get("current_mahadasha"):
        current_dasha_info = {
            "mahadasha": {
                "planet": current["current_mahadasha"].planet,
                "start_date": current["current_mahadasha"].start_date.strftime("%Y-%m-%d"),
                "end_date": current["current_mahadasha"].end_date.strftime("%Y-%m-%d")
            },
            "dasha_string": current["dasha_string"]
        }
        
        if current.get("current_antardasha"):
            current_dasha_info["antardasha"] = {
                "planet": current["current_antardasha"].planet,
                "start_date": current["current_antardasha"].start_date.strftime("%Y-%m-%d"),
                "end_date": current["current_antardasha"].end_date.strftime("%Y-%m-%d")
            }

        # Include deeper levels if available (Pratyantardasha and Sookshma)
        if current.get("current_pratyantardasha"):
            current_dasha_info["pratyantardasha"] = {
                "planet": current["current_pratyantardasha"].planet,
                "start_date": current["current_pratyantardasha"].start_date.strftime("%Y-%m-%d"),
                "end_date": current["current_pratyantardasha"].end_date.strftime("%Y-%m-%d")
            }
            
        if current.get("current_sookshma_dasha"):
            current_dasha_info["sookshma_dasha"] = {
                "planet": current["current_sookshma_dasha"].planet,
                "start_date": current["current_sookshma_dasha"].start_date.strftime("%Y-%m-%d"),
                "end_date": current["current_sookshma_dasha"].end_date.strftime("%Y-%m-%d")
            }
    
    return {
        "birth_dasha_lord": balance_info["birth_dasha_lord"],
        "birth_dasha_balance_years": balance_info["balance_years"],
        "birth_nakshatra": balance_info["nakshatra_name"],
        "mahadasha_periods": formatted_periods,
        "current_dasha": current_dasha_info
    }
