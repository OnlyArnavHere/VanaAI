# 🌳 VanaAI

VanaAI is an AI-powered afforestation decision platform tailored for India. It helps individuals, NGOs, and government agencies make data-driven decisions about where to plant trees and which species are most likely to thrive.

## 🌟 Features

By simply clicking a location on the interactive map, VanaAI analyzes multiple ecological datasets in real-time to provide:

1.  **Ecological Fitness Score (0–100):** A composite score evaluating the location's suitability for planting based on soil, climate, existing vegetation, and land use.
2.  **Species Recommendations:** Recommends the top 3 native Indian tree species with 1-year and 5-year survival probability predictions.
3.  **CO₂ Sequestration Potential:** Estimates the carbon capture potential in tonnes per year.
4.  **Constraint Detection:** Identifies nearby infrastructure (roads, buildings) or protected zones that might restrict planting.
5.  **AI Rationale:** Provides a plain-language explanation of the recommendations and ecological conditions, powered by Claude.

## 🏗️ Tech Stack

**Frontend:**
*   React.js + Vite
*   Tailwind CSS v4
*   MapLibre GL JS (100% open-source interactive maps)

**Backend:**
*   Python 3.11 + FastAPI
*   PostgreSQL + PostGIS (Containerized via Docker)
*   SQLAlchemy & GeoAlchemy2

**Data Integrations (APIs):**
*   **Sentinel-2:** NDVI (Vegetation index) via Element84 STAC API
*   **NASA POWER:** Climatology (Rainfall, Temperature)
*   **SoilGrids:** Soil properties (pH, Organic Carbon, Texture)
*   **OpenStreetMap (Overpass):** Land use, buildings, and infrastructure
*   **GBIF:** Species occurrences data

## 🚀 Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python (3.11+)
*   Docker & Docker Compose (optional, for PostGIS database)
*   Anthropic API Key (for AI rationale generation)

### 1. Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Set your API keys (or create a .env file)
export ANTHROPIC_API_KEY="your_api_key_here"

# Start the FastAPI server (Runs on http://localhost:8000)
uvicorn main:app --reload
```

*Note: The project includes a `docker-compose.yml` to spin up the backend and a PostGIS database together if preferred.*

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server (Runs on http://localhost:5173)
npm run dev
```

## 📄 License

This project is open-source.
