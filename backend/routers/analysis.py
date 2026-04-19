"""
Analysis router — POST /api/analyze endpoint.
Orchestrates all data collection services, scoring, survival prediction,
and AI rationale generation.
"""

import asyncio
import uuid
import math
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from schemas import AnalyzeRequest, AnalyzeResponse, FitnessBreakdown
from schemas import SpeciesRecommendation, CO2Potential, GeoJSONFeatureCollection, GeoJSONFeature
from services.satellite import fetch_ndvi
from services.climate import fetch_climate
from services.soil import fetch_soil
from services.landuse import fetch_landuse
from services.gbif import fetch_species
from services.scoring import compute_fitness_score
from services.survival_model import SurvivalModel
from services.ai_reasoning import generate_rationale, stream_rationale

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize the survival model once
survival_model = SurvivalModel()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_location(request: AnalyzeRequest):
    """
    Analyze a location for afforestation potential.

    Collects data from multiple sources in parallel, computes the
    Ecological Fitness Score, predicts species survival, and generates
    an AI-powered rationale.
    """
    lat = request.latitude
    lon = request.longitude
    radius = request.radius_meters

    logger.info(f"Analyzing location: ({lat}, {lon}) radius={radius}m")

    # ── Step 1: Fetch all external data in parallel ──
    ndvi_task = fetch_ndvi(lat, lon)
    climate_task = fetch_climate(lat, lon)
    soil_task = fetch_soil(lat, lon)
    landuse_task = fetch_landuse(lat, lon, radius)
    gbif_task = fetch_species(lat, lon)

    ndvi_data, climate_data, soil_data, landuse_data, gbif_data = await asyncio.gather(
        ndvi_task, climate_task, soil_task, landuse_task, gbif_task,
        return_exceptions=False,
    )

    logger.info("All external data collected successfully")

    # ── Step 2: Compute fitness score ──
    score_result = compute_fitness_score(soil_data, climate_data, ndvi_data, landuse_data)
    fitness_score = score_result["fitness_score"]
    fitness_breakdown = score_result["fitness_breakdown"]

    logger.info(f"Fitness score: {fitness_score}")

    # ── Step 3: Predict species survival ──
    species_predictions = survival_model.predict(
        soil_ph=soil_data.get("ph", 6.5),
        annual_rainfall_mm=climate_data.get("annual_rainfall_mm", 800),
        max_temp_c=climate_data.get("max_temp_c", 35),
        ndvi_score=ndvi_data.get("ndvi_mean", 0.35),
        elevation_m=100,  # TODO: get from DEM API
        land_use_type="open" if landuse_data.get("open_land") else "mixed",
    )

    # Take top 3 species
    top_species = species_predictions[:3]

    species_recommendations = [
        SpeciesRecommendation(
            species=sp["species"],
            common_name=sp["common_name"],
            survival_1yr=sp["survival_1yr"],
            survival_5yr=sp["survival_5yr"],
            co2_tonnes_per_year=sp["co2_tonnes_per_year"],
            suitability_reasons=sp["suitability_reasons"],
            constraints=sp["constraints"],
        )
        for sp in top_species
    ]

    # ── Step 4: Compute CO₂ potential ──
    avg_co2 = sum(sp["co2_tonnes_per_year"] for sp in top_species) / max(len(top_species), 1)
    co2_potential = CO2Potential(
        per_100_trees_per_year=round(avg_co2 * 100, 2),
        over_10_years=round(avg_co2 * 100 * 10, 2),
    )

    # ── Step 5: Detect constraints ──
    constraints_detected = _detect_constraints(landuse_data, lat, lon)

    # ── Step 6: Generate planting zone GeoJSON ──
    planting_zones = _generate_planting_zones(lat, lon, radius, fitness_score, landuse_data)

    # ── Step 7: Generate AI rationale ──
    ai_rationale = await generate_rationale(
        lat, lon, soil_data, climate_data, ndvi_data, landuse_data,
        fitness_score, fitness_breakdown, top_species,
    )

    logger.info("Analysis complete")

    return AnalyzeResponse(
        zone_id=str(uuid.uuid4()),
        fitness_score=fitness_score,
        fitness_breakdown=FitnessBreakdown(**fitness_breakdown),
        species_recommendations=species_recommendations,
        total_co2_potential=co2_potential,
        constraints_detected=constraints_detected,
        planting_zones=planting_zones,
        ai_rationale=ai_rationale,
    )


@router.post("/analyze/stream")
async def analyze_location_stream(request: AnalyzeRequest):
    """
    Stream the AI rationale for progressive loading in the UI.
    Returns SSE (Server-Sent Events) with the rationale tokens.
    """
    lat = request.latitude
    lon = request.longitude
    radius = request.radius_meters

    # Collect data (same as above)
    ndvi_data, climate_data, soil_data, landuse_data, gbif_data = await asyncio.gather(
        fetch_ndvi(lat, lon),
        fetch_climate(lat, lon),
        fetch_soil(lat, lon),
        fetch_landuse(lat, lon, radius),
        fetch_species(lat, lon),
    )

    score_result = compute_fitness_score(soil_data, climate_data, ndvi_data, landuse_data)
    fitness_score = score_result["fitness_score"]
    fitness_breakdown = score_result["fitness_breakdown"]

    species_predictions = survival_model.predict(
        soil_ph=soil_data.get("ph", 6.5),
        annual_rainfall_mm=climate_data.get("annual_rainfall_mm", 800),
        max_temp_c=climate_data.get("max_temp_c", 35),
        ndvi_score=ndvi_data.get("ndvi_mean", 0.35),
    )

    async def event_generator():
        async for token in stream_rationale(
            lat, lon, soil_data, climate_data, ndvi_data, landuse_data,
            fitness_score, fitness_breakdown, species_predictions[:3],
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def _detect_constraints(landuse: dict, lat: float, lon: float) -> list[str]:
    """
    Detect planting constraints from land use data.
    Returns human-readable constraint strings.
    """
    constraints = []

    # Road constraints
    for road in landuse.get("roads", [])[:5]:
        dist = road.get("distance_m", 999)
        road_type = road.get("type", "road")
        if dist < 100:
            direction = _get_cardinal_direction(lat, lon, road.get("lat", lat), road.get("lon", lon))
            constraints.append(f"{road_type}_{dist}m_{direction}")

    # Building constraints
    building_count = landuse.get("building_count", 0)
    if building_count > 10:
        constraints.append(f"building_cluster_{building_count}_structures")
    elif building_count > 0:
        nearest = landuse.get("nearest_building_m", 999)
        if nearest < 100:
            constraints.append(f"buildings_{nearest}m_nearby")

    # Protected areas
    for pa in landuse.get("protected_areas", []):
        constraints.append(f"protected_area_{pa.get('name', 'unnamed')}")

    # Infrastructure
    if landuse.get("pipelines"):
        constraints.append("pipeline_detected")
    if landuse.get("power_lines"):
        constraints.append("power_line_detected")

    # Water bodies (not necessarily a constraint, but worth noting)
    for water in landuse.get("water_bodies", []):
        dist = water.get("distance_m", 999)
        if dist < 50:
            constraints.append(f"water_body_{dist}m")

    return constraints


def _get_cardinal_direction(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Get cardinal direction from point 1 to point 2."""
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    if abs(dlat) > abs(dlon):
        return "north" if dlat > 0 else "south"
    else:
        return "east" if dlon > 0 else "west"


def _generate_planting_zones(
    lat: float, lon: float, radius: int, fitness_score: float, landuse: dict
) -> GeoJSONFeatureCollection:
    """
    Generate GeoJSON polygons representing the analyzed planting zone.
    Color-coded by fitness score: green (high), yellow (medium), red (low).
    """
    # Create a circular polygon approximation
    num_points = 32
    delta = radius / 111320  # Approximate degrees for the radius

    ring = []
    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        ring_lat = lat + delta * math.cos(angle)
        ring_lon = lon + delta * math.sin(angle) / math.cos(math.radians(lat))
        ring.append([round(ring_lon, 6), round(ring_lat, 6)])
    ring.append(ring[0])  # Close the ring

    # Determine color based on fitness score
    if fitness_score >= 70:
        color = "#22c55e"  # green
        category = "high"
    elif fitness_score >= 40:
        color = "#eab308"  # yellow
        category = "medium"
    else:
        color = "#ef4444"  # red
        category = "low"

    feature = GeoJSONFeature(
        type="Feature",
        geometry={
            "type": "Polygon",
            "coordinates": [ring],
        },
        properties={
            "fitness_score": fitness_score,
            "color": color,
            "category": category,
            "radius_m": radius,
        },
    )

    return GeoJSONFeatureCollection(
        type="FeatureCollection",
        features=[feature],
    )
