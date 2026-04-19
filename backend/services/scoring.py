"""
Ecological Fitness Score calculation.

Weighted composite of 5 sub-scores:
  - Soil score (25%): pH optimality, organic carbon, sand fraction penalty
  - Climate score (25%): annual rainfall range, temperature extremes
  - Vegetation score (20%): NDVI (low = opportunity, high = already forested)
  - Land use score (20%): penalize buildings, roads, water; reward open land
  - Constraints score (10%): pipelines, power lines, protected zones
"""

import logging

logger = logging.getLogger(__name__)

# Score weights
WEIGHTS = {
    "soil": 0.25,
    "climate": 0.25,
    "vegetation": 0.20,
    "land_use": 0.20,
    "constraints": 0.10,
}


def compute_fitness_score(
    soil_data: dict,
    climate_data: dict,
    ndvi_data: dict,
    landuse_data: dict,
) -> dict:
    """
    Compute the Ecological Fitness Score (0-100) from multi-source data.

    Returns:
        {
            "fitness_score": float,
            "fitness_breakdown": {
                "soil_score": float,
                "climate_score": float,
                "vegetation_score": float,
                "land_use_score": float,
                "constraints_score": float,
            }
        }
    """
    soil_score = _compute_soil_score(soil_data)
    climate_score = _compute_climate_score(climate_data)
    vegetation_score = _compute_vegetation_score(ndvi_data)
    land_use_score = _compute_land_use_score(landuse_data)
    constraints_score = _compute_constraints_score(landuse_data)

    fitness = (
        soil_score * WEIGHTS["soil"]
        + climate_score * WEIGHTS["climate"]
        + vegetation_score * WEIGHTS["vegetation"]
        + land_use_score * WEIGHTS["land_use"]
        + constraints_score * WEIGHTS["constraints"]
    )

    return {
        "fitness_score": round(fitness, 1),
        "fitness_breakdown": {
            "soil_score": round(soil_score, 1),
            "climate_score": round(climate_score, 1),
            "vegetation_score": round(vegetation_score, 1),
            "land_use_score": round(land_use_score, 1),
            "constraints_score": round(constraints_score, 1),
        },
    }


def _compute_soil_score(soil: dict) -> float:
    """
    Score soil quality for tree planting (0-100).
    - pH sweet spot: 6.0–7.0 → 100; deviate → penalty
    - Organic carbon: higher is better (up to 15 g/kg)
    - Sand fraction: >70% is bad (poor water retention)
    """
    ph = soil.get("ph", 6.5)
    oc = soil.get("organic_carbon", 6.0)
    sand = soil.get("sand", 40.0)

    # pH score: 6-7 is ideal (100), 5-8 is okay, <4 or >9 is poor
    if 6.0 <= ph <= 7.0:
        ph_score = 100
    elif 5.5 <= ph < 6.0 or 7.0 < ph <= 7.5:
        ph_score = 80
    elif 5.0 <= ph < 5.5 or 7.5 < ph <= 8.0:
        ph_score = 60
    elif 4.5 <= ph < 5.0 or 8.0 < ph <= 8.5:
        ph_score = 40
    else:
        ph_score = 20

    # Organic carbon score (0-15 g/kg range → 0-100)
    oc_score = min(100, (oc / 15.0) * 100)

    # Sand penalty
    if sand > 80:
        sand_score = 20
    elif sand > 70:
        sand_score = 50
    elif sand > 60:
        sand_score = 70
    else:
        sand_score = 100

    # Weighted: pH=40%, OC=35%, Sand=25%
    return ph_score * 0.40 + oc_score * 0.35 + sand_score * 0.25


def _compute_climate_score(climate: dict) -> float:
    """
    Score climate suitability for Indian afforestation (0-100).
    - Ideal rainfall: 700–1500mm (covers most Indian native species)
    - Temperature: penalize extremes above 45°C or below 0°C
    """
    rainfall = climate.get("annual_rainfall_mm", 800)
    max_temp = climate.get("max_temp_c", 35)
    min_temp = climate.get("min_temp_c", 15)

    # Rainfall score
    if 700 <= rainfall <= 1500:
        rain_score = 100
    elif 500 <= rainfall < 700:
        rain_score = 60 + (rainfall - 500) / 200 * 40
    elif 1500 < rainfall <= 2500:
        rain_score = 80  # High rainfall is fine, just less ideal
    elif 300 <= rainfall < 500:
        rain_score = 30 + (rainfall - 300) / 200 * 30
    elif rainfall > 2500:
        rain_score = 70  # Very high rainfall, some challenges
    else:
        rain_score = 20  # Very arid

    # Temperature extremes penalty
    temp_score = 100
    if max_temp > 45:
        temp_score -= 30
    elif max_temp > 42:
        temp_score -= 15
    if min_temp < 0:
        temp_score -= 20
    elif min_temp < 5:
        temp_score -= 10
    temp_score = max(20, temp_score)

    # 60% rainfall, 40% temperature
    return rain_score * 0.6 + temp_score * 0.4


def _compute_vegetation_score(ndvi: dict) -> float:
    """
    Score planting opportunity from NDVI (0-100).
    Low NDVI (bare soil) = HIGH opportunity for planting = high score.
    High NDVI (dense forest) = already forested = lower priority.

    NDVI ranges:
    - 0.0–0.2: bare soil / urban → score 90 (great opportunity)
    - 0.2–0.4: sparse vegetation → score 80 (good opportunity)
    - 0.4–0.6: moderate vegetation → score 50 (moderate opportunity)
    - 0.6–0.8: dense vegetation → score 30 (low priority)
    - 0.8–1.0: very dense forest → score 15 (already forested)
    """
    ndvi_mean = ndvi.get("ndvi_mean", 0.35)

    if ndvi_mean < 0.1:
        return 85  # Very bare, but might be desert — slight caution
    elif ndvi_mean < 0.2:
        return 90  # Ideal planting opportunity
    elif ndvi_mean < 0.3:
        return 80
    elif ndvi_mean < 0.4:
        return 70
    elif ndvi_mean < 0.5:
        return 55
    elif ndvi_mean < 0.6:
        return 40
    elif ndvi_mean < 0.7:
        return 30
    elif ndvi_mean < 0.8:
        return 20
    else:
        return 15


def _compute_land_use_score(landuse: dict) -> float:
    """
    Score land suitability based on OSM features (0-100).
    - Open land, farmland = high score
    - Dense buildings, industrial = low score
    """
    building_count = landuse.get("building_count", 0)
    road_count = landuse.get("road_count", 0)
    nearest_building = landuse.get("nearest_building_m", 999)
    nearest_road = landuse.get("nearest_road_m", 999)
    land_types = landuse.get("land_use_types", [])

    score = 100

    # Building density penalty
    if building_count > 50:
        score -= 50
    elif building_count > 20:
        score -= 30
    elif building_count > 10:
        score -= 15
    elif building_count > 5:
        score -= 8

    # Proximity penalties
    if nearest_building < 30:
        score -= 15
    elif nearest_building < 100:
        score -= 5

    if nearest_road < 20:
        score -= 10
    elif nearest_road < 50:
        score -= 5

    # Land use type modifiers
    positive_types = {"farmland", "grass", "meadow", "forest", "orchard"}
    negative_types = {"industrial", "commercial", "residential", "retail"}

    for lt in land_types:
        if lt in positive_types:
            score += 5
        elif lt in negative_types:
            score -= 10

    return max(0, min(100, score))


def _compute_constraints_score(landuse: dict) -> float:
    """
    Score constraint-freedom (0-100).
    Protected areas, pipelines, power lines reduce the score.
    """
    score = 100

    protected = landuse.get("protected_areas", [])
    pipelines = landuse.get("pipelines", [])
    power_lines = landuse.get("power_lines", [])
    water = landuse.get("water_bodies", [])

    if protected:
        score -= 40  # Major constraint
    if pipelines:
        score -= 20
    if power_lines:
        score -= 15
    if water:
        # Water nearby is actually good for irrigation, mild penalty for direct overlap
        close_water = [w for w in water if w.get("distance_m", 999) < 50]
        if close_water:
            score -= 10

    return max(0, min(100, score))
