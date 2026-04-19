"""
OpenStreetMap Overpass API client — queries land use, buildings,
roads, water bodies, and protected areas around a location.
"""

import httpx
import logging
import math

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ───────────────────── In-memory cache ─────────────────────
_landuse_cache: dict[str, dict] = {}


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}:{round(lon, 2)}"


async def fetch_landuse(latitude: float, longitude: float, radius_m: int = 500) -> dict:
    """
    Query OSM Overpass for land use features within the specified radius.

    Returns:
        {
            "buildings": [{"lat": ..., "lon": ..., "distance_m": ..., "type": ...}],
            "roads": [{"distance_m": ..., "type": ..., "name": ...}],
            "water_bodies": [...],
            "protected_areas": [...],
            "open_land": bool,
            "land_use_types": ["residential", "farmland", ...],
            "building_count": int,
            "road_count": int,
            "nearest_road_m": float,
            "nearest_building_m": float,
            "source": str
        }
    """
    key = _cache_key(latitude, longitude)
    if key in _landuse_cache:
        logger.info(f"Land use cache hit for {key}")
        return _landuse_cache[key]

    try:
        result = await _query_overpass(latitude, longitude, radius_m)
        _landuse_cache[key] = result
        return result
    except Exception as e:
        logger.error(f"Overpass API failed: {e}")
        return _fallback_landuse(str(e))


async def _query_overpass(lat: float, lon: float, radius_m: int) -> dict:
    """Execute Overpass QL queries for different feature types."""
    query = f"""
    [out:json][timeout:25];
    (
      way["highway"](around:{radius_m},{lat},{lon});
      way["building"](around:{radius_m},{lat},{lon});
      way["natural"="water"](around:{radius_m},{lat},{lon});
      relation["natural"="water"](around:{radius_m},{lat},{lon});
      way["boundary"="protected_area"](around:{radius_m},{lat},{lon});
      relation["boundary"="protected_area"](around:{radius_m},{lat},{lon});
      way["landuse"](around:{radius_m},{lat},{lon});
      node["natural"="tree"](around:{radius_m},{lat},{lon});
      way["pipeline"](around:{radius_m},{lat},{lon});
      way["power"="line"](around:{radius_m},{lat},{lon});
    );
    out center;
    """

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(OVERPASS_URL, data={"data": query})
        resp.raise_for_status()
        data = resp.json()

    elements = data.get("elements", [])

    buildings = []
    roads = []
    water_bodies = []
    protected_areas = []
    land_use_types = set()
    pipelines = []
    power_lines = []
    trees = 0

    for el in elements:
        tags = el.get("tags", {})
        center = el.get("center", {})
        el_lat = center.get("lat") or el.get("lat", lat)
        el_lon = center.get("lon") or el.get("lon", lon)
        dist = _haversine(lat, lon, el_lat, el_lon)

        if "building" in tags:
            buildings.append({
                "distance_m": round(dist),
                "type": tags.get("building", "yes"),
                "lat": el_lat,
                "lon": el_lon,
            })
        elif "highway" in tags:
            roads.append({
                "distance_m": round(dist),
                "type": tags.get("highway", "unclassified"),
                "name": tags.get("name", ""),
            })
        elif tags.get("natural") == "water":
            water_bodies.append({
                "distance_m": round(dist),
                "type": tags.get("water", "lake"),
                "name": tags.get("name", ""),
            })
        elif tags.get("boundary") == "protected_area":
            protected_areas.append({
                "distance_m": round(dist),
                "name": tags.get("name", "Protected Area"),
                "protection_title": tags.get("protection_title", ""),
            })
        elif tags.get("natural") == "tree":
            trees += 1
        elif "pipeline" in tags:
            pipelines.append({"distance_m": round(dist)})
        elif tags.get("power") == "line":
            power_lines.append({"distance_m": round(dist)})

        if "landuse" in tags:
            land_use_types.add(tags["landuse"])

    nearest_road = min((r["distance_m"] for r in roads), default=999)
    nearest_building = min((b["distance_m"] for b in buildings), default=999)

    return {
        "buildings": buildings[:20],  # Limit to 20 nearest
        "roads": roads[:20],
        "water_bodies": water_bodies,
        "protected_areas": protected_areas,
        "pipelines": pipelines,
        "power_lines": power_lines,
        "existing_trees": trees,
        "land_use_types": list(land_use_types),
        "building_count": len(buildings),
        "road_count": len(roads),
        "nearest_road_m": nearest_road,
        "nearest_building_m": nearest_building,
        "open_land": len(buildings) < 5 and nearest_building > 100,
        "source": "overpass_osm",
    }


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lon points in metres."""
    R = 6371000  # Earth's radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _fallback_landuse(error: str) -> dict:
    """Return a neutral land use profile when OSM is unavailable."""
    return {
        "buildings": [],
        "roads": [],
        "water_bodies": [],
        "protected_areas": [],
        "pipelines": [],
        "power_lines": [],
        "existing_trees": 0,
        "land_use_types": [],
        "building_count": 0,
        "road_count": 0,
        "nearest_road_m": 999,
        "nearest_building_m": 999,
        "open_land": True,
        "source": "fallback_estimate",
        "error": error,
    }
