from fastapi import APIRouter, HTTPException, Query
import requests
from typing import List, Optional

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
HEADERS = {'User-Agent': 'RideShareVITAP-Backend/1.0'}


def _format_name(address: dict, display_name: str) -> str:
    """Format Nominatim address dict into a clean readable name."""
    if not address:
        parts = display_name.split(',')
        return ', '.join(p.strip() for p in parts[:2])

    primary = (
        address.get('amenity') or address.get('building') or address.get('tourism') or
        address.get('shop') or address.get('road') or address.get('neighbourhood') or
        address.get('suburb') or address.get('village') or address.get('town') or
        address.get('city_district') or address.get('city')
    )
    secondary = (
        address.get('county') or address.get('district') or
        address.get('city') or address.get('town')
    )
    state = address.get('state')

    if primary and secondary and state:
        if primary == secondary:
            return f"{primary}, {state}"
        return f"{primary}, {secondary}, {state}"
    if primary and state:
        return f"{primary}, {state}"
    if primary and secondary:
        return f"{primary}, {secondary}"
    if primary:
        return primary

    parts = display_name.split(',')
    return ', '.join(p.strip() for p in parts[:2])


def _format_subtitle(address: dict) -> str:
    """Format a short secondary description."""
    if not address:
        return ''
    parts = [
        address.get('county') or address.get('district') or address.get('city'),
        address.get('state')
    ]
    return ', '.join(p for p in parts if p)


@router.get("/search")
async def search_locations(q: str = Query(...)):
    try:
        url = f"{NOMINATIM_BASE_URL}/search?q={q}&format=json&limit=10&addressdetails=1&accept-language=en&countrycodes=in"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Nominatim search failed")

        data = response.json()
        results = []
        seen = set()
        for item in data:
            addr = item.get("address") or {}
            name = _format_name(addr, item.get("display_name", ""))
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "id": item.get("place_id"),
                "name": name,
                "subtitle": _format_subtitle(addr),
                "fullAddress": item.get("display_name", ""),
                "latitude": float(item.get("lat")),
                "longitude": float(item.get("lon")),
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# In-memory cache for reverse geocoding to avoid rate limits
REVERSE_CACHE = {}

@router.get("/reverse")
async def reverse_geocode(lat: float = Query(...), lng: float = Query(...)):
    try:
        # Round to 4 decimal places (~11 meters) to improve cache hits
        cache_key = (round(lat, 4), round(lng, 4))
        if cache_key in REVERSE_CACHE:
            return REVERSE_CACHE[cache_key]

        url = f"{NOMINATIM_BASE_URL}/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1&accept-language=en"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 429:
            # If we hit a rate limit, return a generic location instead of failing
            return {
                "name": "Current Location",
                "subtitle": f"{lat:.4f}, {lng:.4f}",
                "latitude": lat,
                "longitude": lng,
            }

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Nominatim reverse geocoding failed")

        data = response.json()
        addr = data.get("address") or {}
        name = _format_name(addr, data.get("display_name", ""))
        
        result = {
            "name": name,
            "subtitle": _format_subtitle(addr),
            "latitude": lat,
            "longitude": lng,
        }
        
        # Save to cache
        REVERSE_CACHE[cache_key] = result
        # Simple cache size limit
        if len(REVERSE_CACHE) > 1000:
            REVERSE_CACHE.clear()
            
        return result
    except Exception as e:
        # Fallback for any error to keep the app working
        return {
            "name": "Location Selected",
            "subtitle": f"{lat:.4f}, {lng:.4f}",
            "latitude": lat,
            "longitude": lng,
        }

