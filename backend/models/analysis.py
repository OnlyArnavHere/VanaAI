"""
Analysis result model — stores completed analysis records.
"""

import uuid
from sqlalchemy import Column, String, Float, JSON, DateTime, func
from database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False)
    fitness_score = Column(Float, nullable=True)
    fitness_breakdown = Column(JSON, nullable=True)
    species_recommendations = Column(JSON, nullable=True)
    co2_potential = Column(JSON, nullable=True)
    constraints_detected = Column(JSON, nullable=True)
    planting_zones_geojson = Column(JSON, nullable=True)
    ai_rationale = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
