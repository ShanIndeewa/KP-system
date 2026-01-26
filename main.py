"""
KP Astrology REST API Backend

A production-ready REST API for Krishnamurti Padhdhati (KP) Astrology calculations.

Features:
- KP New Ayanamsa (Prof. K. Balachandran formula)
- Placidus House System
- Complete Sign/Star/Sub lord calculations
- Sri Lanka location database
- Swiss Ephemeris for accurate planetary positions

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# Create FastAPI application
app = FastAPI(
    title="KP Astrology API",
    description="""
## Krishnamurti Padhdhati (KP) Astrology REST API

A comprehensive API for KP astrological calculations based on the teachings of 
**Prof. K.S. Krishnamurti**.

### Features

- **KP New Ayanamsa**: Uses the exact formula from Prof. K. Balachandran (KP & Astrology Year Book 2003)
- **Placidus House System**: Semi-Arc system as specified by KP methodology
- **Complete Lordship Hierarchy**: Sign Lord → Star Lord → Sub Lord → Sub-Sub Lord
- **Sri Lanka Locations**: Pre-configured database of 25+ Sri Lankan cities
- **High Accuracy**: Swiss Ephemeris (pyswisseph) for planetary calculations

### Calculation Details

- **Ayanamsa Formula**: NKPA = B + [T × P + (T² × A)] / 3600
  - Base (B): 22°22'15.7" at Jan 1, 1900
  - Precession (P): 50.2388475"/year (Newcomb's)
  - Adjustment (A): 0.000111"/year²

- **Vimshottari Dasha Order**: Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury

- **Planets Calculated**: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu

### Usage

Use the `/calculate` endpoint with either:
1. Sri Lanka location key (e.g., `"location": "colombo"`)
2. Direct coordinates with latitude, longitude, and timezone
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["KP Astrology"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "KP Astrology API",
        "version": "1.0.0",
        "description": "Krishnamurti Padhdhati Astrology Calculation System",
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "calculate": "POST /api/v1/calculate",
            "locations": "GET /api/v1/locations",
            "ayanamsa": "GET /api/v1/ayanamsa?date=YYYY-MM-DD"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
