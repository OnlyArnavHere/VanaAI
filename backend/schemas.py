"""
Pydantic request/response schemas for the VanaAI API.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ───────────────────── Request Schemas ─────────────────────

class AnalyzeRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the target point")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the target point")
    radius_meters: int = Field(500, ge=50, le=5000, description="Analysis radius in metres")


# ───────────────────── Nested Response Schemas ─────────────────────

class FitnessBreakdown(BaseModel):
    soil_score: float = Field(..., ge=0, le=100)
    climate_score: float = Field(..., ge=0, le=100)
    vegetation_score: float = Field(..., ge=0, le=100)
    land_use_score: float = Field(..., ge=0, le=100)
    constraints_score: float = Field(..., ge=0, le=100)


class SpeciesRecommendation(BaseModel):
    species: str
    common_name: str
    survival_1yr: float = Field(..., ge=0, le=1)
    survival_5yr: float = Field(..., ge=0, le=1)
    co2_tonnes_per_year: float
    suitability_reasons: list[str]
    constraints: list[str]


class CO2Potential(BaseModel):
    per_100_trees_per_year: float
    over_10_years: float


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict = {}


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature] = []


# ───────────────────── Main Response Schema ─────────────────────

class AnalyzeResponse(BaseModel):
    zone_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fitness_score: float
    fitness_breakdown: FitnessBreakdown
    species_recommendations: list[SpeciesRecommendation]
    total_co2_potential: CO2Potential
    constraints_detected: list[str]
    planting_zones: GeoJSONFeatureCollection
    ai_rationale: str = ""


# ───────────────────── Species Listing ─────────────────────

class SpeciesInfo(BaseModel):
    species: str
    common_name: str
    family: str
    native_region: str
    max_height_m: float
    co2_per_year_kg: float
    preferred_rainfall_mm: tuple[float, float]
    preferred_temp_c: tuple[float, float]
    preferred_soil_ph: tuple[float, float]
    drought_tolerance: str  # "low", "medium", "high"
    growth_rate: str  # "slow", "medium", "fast"


class SpeciesListResponse(BaseModel):
    species: list[SpeciesInfo]
    count: int
