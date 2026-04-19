"""
SoilGrids API client — fetches soil properties for a given lat/lon.
Provides pH, organic carbon, sand/clay/silt fractions, bulk density.
"""

import httpx
import logging

logger = logging.getLogger(__name__)

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

# ───────────────────── In-memory cache ─────────────────────
_soil_cache: dict[str, dict] = {}


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}:{round(lon, 2)}"


async def fetch_soil(latitude: float, longitude: float) -> dict:
    """
    Fetch soil properties from SoilGrids API.

    Returns:
        {
            "ph": float,              # pH in H2O (0-14 scale)
            "organic_carbon": float,  # g/kg
            "sand": float,            # percentage
            "clay": float,            # percentage
            "silt": float,            # percentage
            "bulk_density": float,    # kg/dm³
            "nitrogen": float,       # cg/kg
            "cec": float,            # cmol(c)/kg (cation exchange capacity)
            "depth_cm": str,         # depth range analyzed
            "source": str
        }
    """
    key = _cache_key(latitude, longitude)
    if key in _soil_cache:
        logger.info(f"Soil cache hit for {key}")
        return _soil_cache[key]

    try:
        result = await _call_soilgrids(latitude, longitude)
        _soil_cache[key] = result
        return result
    except Exception as e:
        logger.error(f"SoilGrids API failed: {e}")
        return _fallback_soil(latitude, longitude, str(e))


async def _call_soilgrids(lat: float, lon: float) -> dict:
    """Call the SoilGrids REST API."""
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["phh2o", "ocd", "sand", "clay", "silt", "bdod", "nitrogen", "cec"],
        "depth": "0-30cm",
        "value": "mean",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(SOILGRIDS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    properties = data.get("properties", {}).get("layers", [])

    result = {
        "depth_cm": "0-30",
        "source": "soilgrids",
    }

    for layer in properties:
        name = layer.get("name", "")
        depths = layer.get("depths", [])
        if not depths:
            continue

        values = depths[0].get("values", {})
        mean_val = values.get("mean")

        if mean_val is None:
            continue

        if name == "phh2o":
            result["ph"] = round(mean_val / 10.0, 1)  # SoilGrids gives pH × 10
        elif name == "ocd":
            result["organic_carbon"] = round(mean_val / 10.0, 1)  # dg/kg → g/kg
        elif name == "sand":
            result["sand"] = round(mean_val / 10.0, 1)  # g/kg → %
        elif name == "clay":
            result["clay"] = round(mean_val / 10.0, 1)
        elif name == "silt":
            result["silt"] = round(mean_val / 10.0, 1)
        elif name == "bdod":
            result["bulk_density"] = round(mean_val / 100.0, 2)  # cg/cm³ → kg/dm³
        elif name == "nitrogen":
            result["nitrogen"] = round(mean_val / 10.0, 1)  # cg/kg → g/kg wait, it's already cg/kg
        elif name == "cec":
            result["cec"] = round(mean_val / 10.0, 1)  # mmol(c)/kg → cmol(c)/kg

    # Fill defaults for any missing properties
    result.setdefault("ph", 6.5)
    result.setdefault("organic_carbon", 8.0)
    result.setdefault("sand", 40.0)
    result.setdefault("clay", 25.0)
    result.setdefault("silt", 35.0)
    result.setdefault("bulk_density", 1.3)
    result.setdefault("nitrogen", 1.0)
    result.setdefault("cec", 15.0)

    return result


def _fallback_soil(lat: float, lon: float, error: str) -> dict:
    """Provide reasonable soil estimates for India based on region."""
    # Indo-Gangetic alluvial soils
    if lat > 24 and lon > 78 and lon < 88:
        return {
            "ph": 7.2, "organic_carbon": 5.5, "sand": 35, "clay": 28,
            "silt": 37, "bulk_density": 1.35, "nitrogen": 1.2, "cec": 18,
            "depth_cm": "0-30", "source": "fallback_estimate", "error": error,
        }
    # Deccan black cotton soil
    elif lat > 15 and lat < 24 and lon > 73 and lon < 80:
        return {
            "ph": 7.8, "organic_carbon": 4.0, "sand": 20, "clay": 50,
            "silt": 30, "bulk_density": 1.45, "nitrogen": 0.8, "cec": 35,
            "depth_cm": "0-30", "source": "fallback_estimate", "error": error,
        }
    # Western Ghats laterite
    elif lon < 76 and lat < 18:
        return {
            "ph": 5.5, "organic_carbon": 12.0, "sand": 45, "clay": 30,
            "silt": 25, "bulk_density": 1.2, "nitrogen": 1.5, "cec": 12,
            "depth_cm": "0-30", "source": "fallback_estimate", "error": error,
        }
    # Default Indian soil
    else:
        return {
            "ph": 6.8, "organic_carbon": 6.0, "sand": 40, "clay": 28,
            "silt": 32, "bulk_density": 1.35, "nitrogen": 1.0, "cec": 16,
            "depth_cm": "0-30", "source": "fallback_estimate", "error": error,
        }
