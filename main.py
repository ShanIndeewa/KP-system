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
from fastapi.responses import HTMLResponse
from app.api.routes import router

# OpenAPI tag metadata for logical grouping
tags_metadata = [
    {
        "name": "🔮 Chart Calculations",
        "description": "Core KP astrology chart calculation endpoints. Compute planetary positions, house cusps, ascendant, and Vimshottari Dasha.",
    },
    {
        "name": "🎯 Horary Astrology",
        "description": "KP Horary (Prashna) system endpoints. Uses the 249 sub-division system to determine chart timing.",
    },
    {
        "name": "📍 Locations",
        "description": "Sri Lanka location database with pre-configured coordinates for 25+ cities.",
    },
    {
        "name": "🔧 Utilities",
        "description": "Ayanamsa lookup, health checks, and system information.",
    },
]

# Create FastAPI application
app = FastAPI(
    title="KP Astrology API",
    description="""
# Krishnamurti Padhdhati (KP) Astrology REST API

A comprehensive, production-ready API for **KP astrological calculations** based on the teachings of
**Prof. K.S. Krishnamurti**.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **KP New Ayanamsa** | Prof. K. Balachandran formula (KP & Astrology Year Book 2003) |
| **Placidus House System** | Semi-Arc system as specified by KP methodology |
| **Lordship Hierarchy** | Sign Lord → Star Lord → Sub Lord → Sub-Sub Lord |
| **Sri Lanka Locations** | Pre-configured database of 25+ Sri Lankan cities |
| **Swiss Ephemeris** | High-accuracy planetary calculations via pyswisseph |
| **Vimshottari Dasha** | Full Mahadasha → Antardasha → Pratyantardasha → Sukshma |

---

## 📐 Calculation Details

**Ayanamsa Formula:**
```
NKPA = B + [T × P + (T² × A)] / 3600
```
- **B** (Base): 22°22'15.7" at Jan 1, 1900
- **P** (Precession): 50.2388475"/year (Newcomb's)
- **A** (Adjustment): 0.000111"/year²

**Dasha Order:** Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury

**Planets:** Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu

---

## 🚀 Quick Start

Use the `/api/v1/calculate` endpoint with either:
1. A **Sri Lanka location key** (e.g., `"location": "colombo"`)
2. **Direct coordinates** with `latitude`, `longitude`, and `timezone`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "KP Astrology API Support",
    },
    license_info={
        "name": "MIT",
    },
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
app.include_router(router, prefix="/api/v1")

# Root endpoint
@app.get("/", tags=["🔧 Utilities"])
async def root():
    """Root endpoint with API information and navigation links."""
    return {
        "name": "KP Astrology API",
        "version": "1.0.0",
        "description": "Krishnamurti Padhdhati Astrology Calculation System",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "api_docs": "/api-docs"
        },
        "health": "/api/v1/health",
        "endpoints": {
            "calculate": "POST /api/v1/calculate",
            "calculate_horary": "POST /api/v1/calculate-horary",
            "locations": "GET /api/v1/locations",
            "ayanamsa": "GET /api/v1/ayanamsa?date=YYYY-MM-DD",
            "horary_table": "GET /api/v1/horary-table"
        }
    }


# Custom professional API documentation page
@app.get("/api-docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_api_docs():
    """Serve a beautiful custom API documentation page."""
    with open("static/api-docs.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
