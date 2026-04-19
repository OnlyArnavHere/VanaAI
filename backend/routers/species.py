"""
Species router — GET /api/species endpoint.
Returns the database of tracked Indian tree species with ecological profiles.
"""

from fastapi import APIRouter
from services.survival_model import SurvivalModel

router = APIRouter(prefix="/api", tags=["species"])

# Reuse the model instance for species data
_model = SurvivalModel()


@router.get("/species")
async def list_species():
    """
    List all tracked tree species with their ecological profiles.
    """
    species_list = _model.list_species()
    return {
        "species": species_list,
        "count": len(species_list),
    }


@router.get("/species/{species_name}")
async def get_species(species_name: str):
    """
    Get detailed info for a specific species.
    Species name should be the scientific name (e.g., 'Azadirachta indica').
    """
    # Try exact match first
    info = _model.get_species_info(species_name)
    if info:
        return info

    # Try case-insensitive partial match
    for name in _model.species_db:
        if species_name.lower() in name.lower():
            return _model.species_db[name]

    return {"error": f"Species '{species_name}' not found", "available": list(_model.species_db.keys())}


CITIES_DB = [
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "rainfall": 714, "temp": 40, "ph": 7.2},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "rainfall": 2146, "temp": 35, "ph": 6.8},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "rainfall": 900, "temp": 34, "ph": 6.5},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "rainfall": 1400, "temp": 38, "ph": 7.0},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "rainfall": 1600, "temp": 36, "ph": 6.5},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "rainfall": 800, "temp": 39, "ph": 7.5},
    {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "rainfall": 722, "temp": 38, "ph": 6.8},
    {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "rainfall": 600, "temp": 45, "ph": 8.0},
    {"name": "Dehradun", "lat": 30.3165, "lon": 78.0322, "rainfall": 2200, "temp": 35, "ph": 6.0},
    {"name": "Kochi", "lat": 9.9312, "lon": 76.2673, "rainfall": 3000, "temp": 33, "ph": 5.5},
    {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362, "rainfall": 1700, "temp": 32, "ph": 5.8},
    {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126, "rainfall": 1100, "temp": 40, "ph": 7.0},
    {"name": "Shimla", "lat": 31.1048, "lon": 77.1734, "rainfall": 1400, "temp": 28, "ph": 6.2},
    {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "rainfall": 1100, "temp": 39, "ph": 7.1},
]

@router.get("/species/{species_name}/best-locations")
async def get_best_locations(species_name: str):
    """
    Find the best optimal locations to plant a specific species across India.
    """
    info = None
    # Try exact match first
    if species_name in _model.species_db:
        info = _model.species_db[species_name]
    else:
        # Try case-insensitive partial match
        for name in _model.species_db:
            if species_name.lower() in name.lower():
                info = _model.species_db[name]
                break

    if not info:
        return {"error": "Species not found"}
        
    results = []
    for c in CITIES_DB:
        features = {
            "soil_ph": c["ph"],
            "annual_rainfall_mm": c["rainfall"],
            "max_temp_c": c["temp"],
            "ndvi_range": 0.3,
            "elevation_m": 100,
        }
        match_score = _model._compute_match_score(features, info["preferred"])
        survival = info["base_survival_1yr"] * match_score
        
        results.append({
            "name": c["name"],
            "lat": c["lat"],
            "lon": c["lon"],
            "score": int(match_score * 100),
            "survival_prob": round(survival * 100, 1)
        })
        
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]
