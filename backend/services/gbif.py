"""
GBIF species occurrence query — finds tree species observed near a location.
"""

import httpx
import logging

logger = logging.getLogger(__name__)

GBIF_URL = "https://api.gbif.org/v1/occurrence/search"

# ───────────────────── In-memory cache ─────────────────────
_gbif_cache: dict[str, dict] = {}


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 1)}:{round(lon, 1)}"


# Indian native tree species we track
TRACKED_SPECIES = {
    "Azadirachta indica": "Neem",
    "Ficus benghalensis": "Banyan",
    "Ficus religiosa": "Peepal",
    "Mangifera indica": "Mango",
    "Tectona grandis": "Teak",
    "Bambusa vulgaris": "Bamboo",
    "Eucalyptus globulus": "Eucalyptus",
    "Cocos nucifera": "Coconut",
    "Dalbergia sissoo": "Shisham",
    "Terminalia arjuna": "Arjuna",
}


async def fetch_species(latitude: float, longitude: float, radius_km: float = 50) -> dict:
    """
    Query GBIF for tree species occurrences near the location.

    Returns:
        {
            "observed_species": [
                {"species": "Azadirachta indica", "common_name": "Neem", "count": 12},
                ...
            ],
            "total_observations": int,
            "native_species_found": int,
            "source": str
        }
    """
    key = _cache_key(latitude, longitude)
    if key in _gbif_cache:
        logger.info(f"GBIF cache hit for {key}")
        return _gbif_cache[key]

    try:
        result = await _query_gbif(latitude, longitude, radius_km)
        _gbif_cache[key] = result
        return result
    except Exception as e:
        logger.error(f"GBIF API failed: {e}")
        return _fallback_species(str(e))


async def _query_gbif(lat: float, lon: float, radius_km: float) -> dict:
    """Query GBIF occurrence search API."""
    observed = []
    total = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for species_name, common_name in TRACKED_SPECIES.items():
            try:
                params = {
                    "decimalLatitude": f"{lat - 0.5},{lat + 0.5}",
                    "decimalLongitude": f"{lon - 0.5},{lon + 0.5}",
                    "scientificName": species_name,
                    "limit": 5,
                    "hasCoordinate": "true",
                    "country": "IN",
                }
                resp = await client.get(GBIF_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    count = data.get("count", 0)
                    if count > 0:
                        observed.append({
                            "species": species_name,
                            "common_name": common_name,
                            "count": count,
                        })
                        total += count
            except Exception:
                continue  # Skip individual species failures

    # Sort by count descending
    observed.sort(key=lambda x: x["count"], reverse=True)

    return {
        "observed_species": observed,
        "total_observations": total,
        "native_species_found": len(observed),
        "source": "gbif",
    }


def _fallback_species(error: str) -> dict:
    """Return common Indian tree species as fallback."""
    return {
        "observed_species": [
            {"species": "Azadirachta indica", "common_name": "Neem", "count": 0},
            {"species": "Ficus religiosa", "common_name": "Peepal", "count": 0},
            {"species": "Mangifera indica", "common_name": "Mango", "count": 0},
        ],
        "total_observations": 0,
        "native_species_found": 3,
        "source": "fallback_estimate",
        "error": error,
    }
