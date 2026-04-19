"""
NASA POWER API client — fetches climatology data for a given lat/lon.
Provides temperature, precipitation, solar radiation, and humidity.
"""

import httpx
import logging

logger = logging.getLogger(__name__)

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"

# ───────────────────── In-memory cache ─────────────────────
_climate_cache: dict[str, dict] = {}


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}:{round(lon, 2)}"


async def fetch_climate(latitude: float, longitude: float) -> dict:
    """
    Fetch climatology data from NASA POWER API.

    Returns:
        {
            "annual_rainfall_mm": float,
            "avg_temp_c": float,
            "max_temp_c": float,
            "min_temp_c": float,
            "relative_humidity": float,
            "solar_radiation": float,
            "monthly_rainfall": dict,
            "monthly_temp": dict,
            "source": str
        }
    """
    key = _cache_key(latitude, longitude)
    if key in _climate_cache:
        logger.info(f"Climate cache hit for {key}")
        return _climate_cache[key]

    try:
        result = await _call_nasa_power(latitude, longitude)
        _climate_cache[key] = result
        return result
    except Exception as e:
        logger.error(f"NASA POWER API failed: {e}")
        return _fallback_climate(latitude, longitude, str(e))


async def _call_nasa_power(lat: float, lon: float) -> dict:
    """Call the NASA POWER climatology endpoint."""
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN",
        "community": "ag",
        "longitude": lon,
        "latitude": lat,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(NASA_POWER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    props = data.get("properties", {}).get("parameter", {})

    # Extract annual values (key "ANN" in the response)
    t2m = props.get("T2M", {})
    t2m_max = props.get("T2M_MAX", {})
    t2m_min = props.get("T2M_MIN", {})
    precip = props.get("PRECTOTCORR", {})
    humidity = props.get("RH2M", {})
    solar = props.get("ALLSKY_SFC_SW_DWN", {})

    # Monthly rainfall for seasonality analysis
    monthly_rainfall = {}
    monthly_temp = {}
    month_keys = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    for m in month_keys:
        monthly_rainfall[m] = round(precip.get(m, 0) * 30, 1)  # mm/day → mm/month
        monthly_temp[m] = round(t2m.get(m, 25), 1)

    annual_rainfall = sum(monthly_rainfall.values())

    return {
        "annual_rainfall_mm": round(annual_rainfall, 1),
        "avg_temp_c": round(t2m.get("ANN", 26), 1),
        "max_temp_c": round(t2m_max.get("ANN", 35), 1),
        "min_temp_c": round(t2m_min.get("ANN", 18), 1),
        "relative_humidity": round(humidity.get("ANN", 60), 1),
        "solar_radiation": round(solar.get("ANN", 5.0), 2),
        "monthly_rainfall": monthly_rainfall,
        "monthly_temp": monthly_temp,
        "source": "nasa_power",
    }


def _fallback_climate(lat: float, lon: float, error: str) -> dict:
    """Provide reasonable Indian climate estimates based on geography."""
    # India spans roughly 8°N to 37°N
    if lat > 30:  # Northern India (Himalayan foothills)
        rainfall, avg_t, max_t, min_t = 1200, 22, 38, 5
    elif lat > 23:  # Central-North India (Indo-Gangetic plain)
        rainfall, avg_t, max_t, min_t = 900, 26, 42, 10
    elif lat > 18:  # Central India (Deccan)
        rainfall, avg_t, max_t, min_t = 800, 27, 40, 14
    elif lon < 76:  # Western coast / Western Ghats
        rainfall, avg_t, max_t, min_t = 2500, 27, 35, 20
    else:  # Southern / Eastern India
        rainfall, avg_t, max_t, min_t = 1100, 28, 37, 18

    return {
        "annual_rainfall_mm": rainfall,
        "avg_temp_c": avg_t,
        "max_temp_c": max_t,
        "min_temp_c": min_t,
        "relative_humidity": 65,
        "solar_radiation": 5.2,
        "monthly_rainfall": {},
        "monthly_temp": {},
        "source": "fallback_estimate",
        "error": error,
    }
