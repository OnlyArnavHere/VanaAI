"""
Claude API integration for AI-powered rationale generation.
Uses Anthropic's Claude API to produce plain-language explanations
of afforestation recommendations.
"""

import os
import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-5-20250229"

SYSTEM_PROMPT = """You are an expert Indian forester and ecologist working for VanaAI, \
an afforestation decision platform. Given ecological data about a location in India, \
explain in 150 words why specific tree species are recommended. Be specific about the data. \
Speak in plain, accessible language that a non-expert can understand. \
Focus on actionable insights. \
Do NOT use markdown formatting — write in plain prose paragraphs."""


async def generate_rationale(
    latitude: float,
    longitude: float,
    soil_data: dict,
    climate_data: dict,
    ndvi_data: dict,
    landuse_data: dict,
    fitness_score: float,
    fitness_breakdown: dict,
    species_recommendations: list[dict],
) -> str:
    """
    Generate a plain-language rationale using Claude.

    Returns the full rationale text. If the API is unavailable,
    returns a rule-based fallback rationale.
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY set — using fallback rationale")
        return _fallback_rationale(
            latitude, longitude, soil_data, climate_data,
            ndvi_data, landuse_data, fitness_score,
            fitness_breakdown, species_recommendations
        )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        user_prompt = _build_user_prompt(
            latitude, longitude, soil_data, climate_data,
            ndvi_data, landuse_data, fitness_score,
            fitness_breakdown, species_recommendations
        )

        message = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return message.content[0].text

    except Exception as e:
        logger.error(f"Claude API failed: {e}")
        return _fallback_rationale(
            latitude, longitude, soil_data, climate_data,
            ndvi_data, landuse_data, fitness_score,
            fitness_breakdown, species_recommendations
        )


async def stream_rationale(
    latitude: float,
    longitude: float,
    soil_data: dict,
    climate_data: dict,
    ndvi_data: dict,
    landuse_data: dict,
    fitness_score: float,
    fitness_breakdown: dict,
    species_recommendations: list[dict],
) -> AsyncIterator[str]:
    """
    Stream the rationale token-by-token using Claude's streaming API.
    Falls back to yielding the full fallback text if API unavailable.
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY — streaming fallback rationale")
        text = _fallback_rationale(
            latitude, longitude, soil_data, climate_data,
            ndvi_data, landuse_data, fitness_score,
            fitness_breakdown, species_recommendations
        )
        # Simulate streaming by yielding words
        for word in text.split(" "):
            yield word + " "
        return

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        user_prompt = _build_user_prompt(
            latitude, longitude, soil_data, climate_data,
            ndvi_data, landuse_data, fitness_score,
            fitness_breakdown, species_recommendations
        )

        with client.messages.stream(
            model=MODEL,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    except Exception as e:
        logger.error(f"Claude streaming failed: {e}")
        text = _fallback_rationale(
            latitude, longitude, soil_data, climate_data,
            ndvi_data, landuse_data, fitness_score,
            fitness_breakdown, species_recommendations
        )
        for word in text.split(" "):
            yield word + " "


def _build_user_prompt(
    lat: float, lon: float,
    soil: dict, climate: dict, ndvi: dict, landuse: dict,
    fitness: float, breakdown: dict, species: list[dict],
) -> str:
    """Build the detailed context prompt for Claude."""
    top_species = species[:3] if species else []
    species_text = "\n".join([
        f"  - {s['common_name']} ({s['species']}): "
        f"1yr survival {s['survival_1yr']:.0%}, 5yr survival {s['survival_5yr']:.0%}, "
        f"CO₂ {s['co2_tonnes_per_year']} tonnes/yr"
        for s in top_species
    ])

    constraints = landuse.get("protected_areas", [])
    constraint_text = "None detected" if not constraints else str(constraints)

    return f"""Analyze this location for tree planting and explain your recommendations:

Location: {lat}°N, {lon}°E (India)
Overall Fitness Score: {fitness}/100

Soil Data (0-30cm depth):
  - pH: {soil.get('ph', 'N/A')}
  - Organic Carbon: {soil.get('organic_carbon', 'N/A')} g/kg
  - Sand: {soil.get('sand', 'N/A')}%, Clay: {soil.get('clay', 'N/A')}%, Silt: {soil.get('silt', 'N/A')}%
  - Soil Score: {breakdown.get('soil_score', 'N/A')}/100

Climate Data:
  - Annual Rainfall: {climate.get('annual_rainfall_mm', 'N/A')} mm
  - Average Temperature: {climate.get('avg_temp_c', 'N/A')}°C
  - Max Temperature: {climate.get('max_temp_c', 'N/A')}°C
  - Min Temperature: {climate.get('min_temp_c', 'N/A')}°C
  - Climate Score: {breakdown.get('climate_score', 'N/A')}/100

Vegetation:
  - NDVI (satellite): {ndvi.get('ndvi_mean', 'N/A')}
  - Vegetation Score: {breakdown.get('vegetation_score', 'N/A')}/100

Land Use (OSM):
  - Buildings nearby: {landuse.get('building_count', 0)}
  - Roads nearby: {landuse.get('road_count', 0)}
  - Nearest building: {landuse.get('nearest_building_m', 'N/A')}m
  - Open land: {landuse.get('open_land', 'unknown')}
  - Land Use Score: {breakdown.get('land_use_score', 'N/A')}/100

Protected Areas / Constraints: {constraint_text}
Constraints Score: {breakdown.get('constraints_score', 'N/A')}/100

Top Species Recommendations:
{species_text}

Explain why these species are recommended for this location. Mention specific data points. \
Note any planting considerations or risks. Keep it to 150 words."""


def _fallback_rationale(
    lat: float, lon: float,
    soil: dict, climate: dict, ndvi: dict, landuse: dict,
    fitness: float, breakdown: dict, species: list[dict],
) -> str:
    """Generate a rule-based rationale when Claude is unavailable."""
    top = species[0] if species else {"common_name": "Neem", "species": "Azadirachta indica"}
    ph = soil.get("ph", 6.5)
    rainfall = climate.get("annual_rainfall_mm", 800)
    ndvi_val = ndvi.get("ndvi_mean", 0.35)
    buildings = landuse.get("building_count", 0)

    # Build a contextual explanation
    parts = [
        f"This zone at {lat:.3f}°N, {lon:.3f}°E scores {fitness:.0f}/100 for afforestation potential."
    ]

    # Soil commentary
    if ph < 5.5:
        parts.append(f"The acidic soil (pH {ph}) favours acid-tolerant species.")
    elif ph > 7.5:
        parts.append(f"The alkaline soil (pH {ph}) suits species like Neem that tolerate high pH.")
    else:
        parts.append(f"The soil pH of {ph} is in the optimal range for most native species.")

    # Rainfall commentary
    if rainfall < 500:
        parts.append(f"With only {rainfall:.0f}mm annual rainfall, drought-tolerant species are essential.")
    elif rainfall > 1500:
        parts.append(f"The {rainfall:.0f}mm annual rainfall supports moisture-loving species.")
    else:
        parts.append(f"Annual rainfall of {rainfall:.0f}mm is adequate for most Indian native trees.")

    # NDVI commentary
    if ndvi_val < 0.2:
        parts.append("Satellite imagery shows bare or sparsely vegetated land — ideal for new planting.")
    elif ndvi_val > 0.5:
        parts.append("The area already has moderate vegetation cover. Enrichment planting is recommended.")
    else:
        parts.append("Moderate vegetation cover suggests opportunity for supplemental planting.")

    # Land use commentary
    if buildings > 10:
        parts.append(f"The presence of {buildings} buildings nearby requires careful site selection within the zone.")
    elif landuse.get("open_land"):
        parts.append("The area is predominantly open land, providing ample planting space.")

    # Species recommendation
    parts.append(
        f"We recommend {top['common_name']} ({top['species']}) as the primary species "
        f"due to its strong ecological match with local conditions."
    )

    return " ".join(parts)
