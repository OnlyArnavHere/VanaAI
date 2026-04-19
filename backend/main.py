"""
VanaAI Backend — FastAPI Application Entry Point.

AI-powered afforestation decision platform for India.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analysis, species

# ───────────────────── Logging ─────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("vanai")


# ───────────────────── Lifespan ─────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🌳 VanaAI backend starting up...")
    # Database init is optional — works without PostGIS for MVP
    try:
        from database import init_db
        init_db()
        logger.info("Database initialised")
    except Exception as e:
        logger.warning(f"Database not available (running without PostGIS): {e}")
    yield
    logger.info("VanaAI backend shutting down")


# ───────────────────── App ─────────────────────
app = FastAPI(
    title="VanaAI",
    description="AI-powered afforestation decision platform for India",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────── Routers ─────────────────────
app.include_router(analysis.router)
app.include_router(species.router)


# ───────────────────── Health Check ─────────────────────
@app.get("/")
async def root():
    return {
        "name": "VanaAI",
        "version": "0.1.0",
        "description": "AI-powered afforestation decision platform for India",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "species": "GET /api/species",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "vanai-backend"}
