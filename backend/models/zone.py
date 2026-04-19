"""
PostGIS zone model — spatial geometry for analyzed zones.
"""

import uuid
from sqlalchemy import Column, String, Float, DateTime, func
from geoalchemy2 import Geometry
from database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False, default=500)
    geom = Column(Geometry("POLYGON", srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
