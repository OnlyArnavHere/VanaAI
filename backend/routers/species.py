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
