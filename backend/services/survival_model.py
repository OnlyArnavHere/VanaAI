"""
Survival prediction model for tree species.

MVP: Rule-based model with the same interface as an XGBoost model.
Computes 1-year and 5-year survival probabilities based on ecological
feature ranges for each species.

Ready to be swapped with a real trained XGBoost model when training data
becomes available.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ───────────────────── Species Database ─────────────────────

SPECIES_DB = {
    "Azadirachta indica": {
        "common_name": "Neem",
        "family": "Meliaceae",
        "native_region": "Indian subcontinent",
        "max_height_m": 20,
        "co2_per_year_kg": 23,
        "base_survival_1yr": 0.90,
        "base_survival_5yr": 0.78,
        "growth_rate": "fast",
        "drought_tolerance": "high",
        "preferred": {
            "soil_ph": (5.0, 8.5),
            "annual_rainfall_mm": (400, 1200),
            "max_temp_c": (25, 48),
            "ndvi_range": (0.0, 0.5),
            "elevation_m": (0, 700),
        },
        "traits": ["drought tolerant", "poor soil tolerant", "fast growing", "medicinal"],
    },
    "Ficus benghalensis": {
        "common_name": "Banyan",
        "family": "Moraceae",
        "native_region": "Indian subcontinent",
        "max_height_m": 25,
        "co2_per_year_kg": 35,
        "base_survival_1yr": 0.85,
        "base_survival_5yr": 0.72,
        "growth_rate": "medium",
        "drought_tolerance": "medium",
        "preferred": {
            "soil_ph": (5.5, 7.5),
            "annual_rainfall_mm": (600, 2000),
            "max_temp_c": (20, 42),
            "ndvi_range": (0.1, 0.6),
            "elevation_m": (0, 1200),
        },
        "traits": ["shade providing", "native heritage", "long-lived", "aerial roots"],
    },
    "Ficus religiosa": {
        "common_name": "Peepal",
        "family": "Moraceae",
        "native_region": "Indian subcontinent",
        "max_height_m": 30,
        "co2_per_year_kg": 30,
        "base_survival_1yr": 0.88,
        "base_survival_5yr": 0.76,
        "growth_rate": "fast",
        "drought_tolerance": "high",
        "preferred": {
            "soil_ph": (5.0, 8.0),
            "annual_rainfall_mm": (500, 1800),
            "max_temp_c": (22, 45),
            "ndvi_range": (0.0, 0.5),
            "elevation_m": (0, 1500),
        },
        "traits": ["drought tolerant", "sacred tree", "high O₂ output", "long-lived"],
    },
    "Mangifera indica": {
        "common_name": "Mango",
        "family": "Anacardiaceae",
        "native_region": "South Asia",
        "max_height_m": 40,
        "co2_per_year_kg": 28,
        "base_survival_1yr": 0.82,
        "base_survival_5yr": 0.68,
        "growth_rate": "medium",
        "drought_tolerance": "medium",
        "preferred": {
            "soil_ph": (5.5, 7.5),
            "annual_rainfall_mm": (600, 2500),
            "max_temp_c": (24, 40),
            "ndvi_range": (0.1, 0.5),
            "elevation_m": (0, 600),
        },
        "traits": ["fruit bearing", "shade providing", "commercially valuable", "native"],
    },
    "Tectona grandis": {
        "common_name": "Teak",
        "family": "Lamiaceae",
        "native_region": "South & Southeast Asia",
        "max_height_m": 40,
        "co2_per_year_kg": 22,
        "base_survival_1yr": 0.80,
        "base_survival_5yr": 0.65,
        "growth_rate": "slow",
        "drought_tolerance": "medium",
        "preferred": {
            "soil_ph": (6.0, 7.5),
            "annual_rainfall_mm": (800, 2500),
            "max_temp_c": (25, 42),
            "ndvi_range": (0.1, 0.6),
            "elevation_m": (0, 1000),
        },
        "traits": ["valuable timber", "termite resistant", "deciduous", "well-drained soil"],
    },
    "Bambusa vulgaris": {
        "common_name": "Bamboo",
        "family": "Poaceae",
        "native_region": "Tropical Asia",
        "max_height_m": 20,
        "co2_per_year_kg": 40,
        "base_survival_1yr": 0.92,
        "base_survival_5yr": 0.85,
        "growth_rate": "fast",
        "drought_tolerance": "low",
        "preferred": {
            "soil_ph": (5.0, 7.0),
            "annual_rainfall_mm": (800, 3000),
            "max_temp_c": (20, 38),
            "ndvi_range": (0.1, 0.5),
            "elevation_m": (0, 1500),
        },
        "traits": ["fastest growing", "high CO₂ capture", "erosion control", "versatile use"],
    },
    "Eucalyptus globulus": {
        "common_name": "Eucalyptus",
        "family": "Myrtaceae",
        "native_region": "Australia (naturalised in India)",
        "max_height_m": 55,
        "co2_per_year_kg": 25,
        "base_survival_1yr": 0.88,
        "base_survival_5yr": 0.75,
        "growth_rate": "fast",
        "drought_tolerance": "high",
        "preferred": {
            "soil_ph": (4.5, 7.5),
            "annual_rainfall_mm": (400, 1500),
            "max_temp_c": (20, 42),
            "ndvi_range": (0.0, 0.5),
            "elevation_m": (0, 2000),
        },
        "traits": ["fast growing", "drought tolerant", "paper industry", "caution: water table"],
    },
    "Cocos nucifera": {
        "common_name": "Coconut",
        "family": "Arecaceae",
        "native_region": "Tropical coastal regions",
        "max_height_m": 30,
        "co2_per_year_kg": 18,
        "base_survival_1yr": 0.78,
        "base_survival_5yr": 0.62,
        "growth_rate": "slow",
        "drought_tolerance": "low",
        "preferred": {
            "soil_ph": (5.5, 7.0),
            "annual_rainfall_mm": (1000, 3000),
            "max_temp_c": (25, 38),
            "ndvi_range": (0.1, 0.5),
            "elevation_m": (0, 100),
        },
        "traits": ["coastal species", "fruit bearing", "salt tolerant", "tropical only"],
    },
    "Dalbergia sissoo": {
        "common_name": "Shisham",
        "family": "Fabaceae",
        "native_region": "Indian subcontinent",
        "max_height_m": 25,
        "co2_per_year_kg": 20,
        "base_survival_1yr": 0.84,
        "base_survival_5yr": 0.70,
        "growth_rate": "fast",
        "drought_tolerance": "medium",
        "preferred": {
            "soil_ph": (5.5, 8.0),
            "annual_rainfall_mm": (500, 2000),
            "max_temp_c": (20, 44),
            "ndvi_range": (0.0, 0.5),
            "elevation_m": (0, 1000),
        },
        "traits": ["nitrogen fixing", "valuable timber", "riverine species", "fast growing"],
    },
    "Terminalia arjuna": {
        "common_name": "Arjuna",
        "family": "Combretaceae",
        "native_region": "Indian subcontinent",
        "max_height_m": 25,
        "co2_per_year_kg": 22,
        "base_survival_1yr": 0.86,
        "base_survival_5yr": 0.73,
        "growth_rate": "medium",
        "drought_tolerance": "medium",
        "preferred": {
            "soil_ph": (6.0, 7.5),
            "annual_rainfall_mm": (600, 1800),
            "max_temp_c": (22, 42),
            "ndvi_range": (0.1, 0.5),
            "elevation_m": (0, 900),
        },
        "traits": ["medicinal bark", "riverbank species", "soil conservation", "native"],
    },
}


class SurvivalModel:
    """
    MVP rule-based survival prediction model.

    Interface is designed to be drop-in compatible with a future
    XGBoost-based model. Call .predict() with ecological features
    and get back survival probabilities per species.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the model.
        In the future, model_path will point to a trained XGBoost model file.
        """
        self.model_type = "rule_based"
        self.species_db = SPECIES_DB
        self.is_trained = True  # Rule-based model is always "trained"
        logger.info(f"SurvivalModel initialized (type={self.model_type})")

    def predict(
        self,
        soil_ph: float,
        annual_rainfall_mm: float,
        max_temp_c: float,
        ndvi_score: float,
        elevation_m: float = 100,
        land_use_type: str = "open",
    ) -> list[dict]:
        """
        Predict survival probabilities for all species given ecological features.

        Returns a list of species with survival scores, sorted by 1-year survival
        descending (top recommendations first).
        """
        features = {
            "soil_ph": soil_ph,
            "annual_rainfall_mm": annual_rainfall_mm,
            "max_temp_c": max_temp_c,
            "ndvi_range": ndvi_score,
            "elevation_m": elevation_m,
        }

        results = []
        for species_name, spec in self.species_db.items():
            match_score = self._compute_match_score(features, spec["preferred"])
            survival_1yr = round(spec["base_survival_1yr"] * match_score, 3)
            survival_5yr = round(spec["base_survival_5yr"] * match_score, 3)
            co2_tonnes = round(spec["co2_per_year_kg"] / 1000, 4)

            # Build suitability reasons
            reasons = self._get_suitability_reasons(features, spec)

            # Build constraint warnings
            constraints = self._get_constraints(features, spec)

            results.append({
                "species": species_name,
                "common_name": spec["common_name"],
                "survival_1yr": survival_1yr,
                "survival_5yr": survival_5yr,
                "co2_tonnes_per_year": co2_tonnes,
                "suitability_reasons": reasons,
                "constraints": constraints,
                "match_score": match_score,
            })

        # Sort by 1-year survival descending
        results.sort(key=lambda x: x["survival_1yr"], reverse=True)
        return results

    def _compute_match_score(self, features: dict, preferred: dict) -> float:
        """
        Compute how well the ecological features match the species' preferred ranges.
        Returns a multiplier between 0.3 and 1.0.
        """
        scores = []

        for feature_name, (low, high) in preferred.items():
            value = features.get(feature_name)
            if value is None:
                scores.append(0.8)  # Neutral if data missing
                continue

            if low <= value <= high:
                # Perfect range: score 1.0
                scores.append(1.0)
            else:
                # How far outside the range?
                range_size = high - low
                if range_size == 0:
                    range_size = 1

                if value < low:
                    deviation = (low - value) / range_size
                else:
                    deviation = (value - high) / range_size

                # Exponential decay: small deviations are okay, large ones are bad
                score = max(0.3, 1.0 - deviation * 0.5)
                scores.append(score)

        # Product of all scores (multiplicative — one bad factor drags everything down)
        result = 1.0
        for s in scores:
            result *= s

        # But don't let it go below 0.3
        return max(0.3, min(1.0, result))

    def _get_suitability_reasons(self, features: dict, spec: dict) -> list[str]:
        """Generate human-readable reasons why this species is suitable."""
        reasons = []
        preferred = spec["preferred"]

        ph = features.get("soil_ph", 6.5)
        if preferred["soil_ph"][0] <= ph <= preferred["soil_ph"][1]:
            reasons.append("suitable soil pH")

        rain = features.get("annual_rainfall_mm", 800)
        if preferred["annual_rainfall_mm"][0] <= rain <= preferred["annual_rainfall_mm"][1]:
            reasons.append("adequate rainfall")

        # Add species-specific traits that match conditions
        if spec.get("drought_tolerance") == "high" and rain < 700:
            reasons.append("drought tolerant")

        if features.get("ndvi_range", 0.3) < 0.3:
            reasons.append("good for bare land restoration")

        # Add general positive traits
        for trait in spec.get("traits", [])[:2]:
            if trait not in reasons:
                reasons.append(trait)

        return reasons[:5]

    def _get_constraints(self, features: dict, spec: dict) -> list[str]:
        """Generate warnings about potential issues for this species."""
        constraints = []
        preferred = spec["preferred"]

        ph = features.get("soil_ph", 6.5)
        if ph < preferred["soil_ph"][0] or ph > preferred["soil_ph"][1]:
            constraints.append(f"soil pH {ph} outside ideal range {preferred['soil_ph']}")

        rain = features.get("annual_rainfall_mm", 800)
        if rain < preferred["annual_rainfall_mm"][0]:
            constraints.append(f"insufficient rainfall ({rain}mm vs {preferred['annual_rainfall_mm'][0]}mm minimum)")
        elif rain > preferred["annual_rainfall_mm"][1]:
            constraints.append(f"excessive rainfall ({rain}mm)")

        temp = features.get("max_temp_c", 35)
        if temp > preferred["max_temp_c"][1]:
            constraints.append(f"temperature too high ({temp}°C)")

        return constraints

    def get_species_info(self, species_name: str) -> Optional[dict]:
        """Get full species information."""
        return self.species_db.get(species_name)

    def list_species(self) -> list[dict]:
        """List all species in the database."""
        return [
            {
                "species": name,
                "common_name": data["common_name"],
                "family": data["family"],
                "native_region": data["native_region"],
                "max_height_m": data["max_height_m"],
                "co2_per_year_kg": data["co2_per_year_kg"],
                "preferred_rainfall_mm": data["preferred"]["annual_rainfall_mm"],
                "preferred_temp_c": data["preferred"]["max_temp_c"],
                "preferred_soil_ph": data["preferred"]["soil_ph"],
                "drought_tolerance": data["drought_tolerance"],
                "growth_rate": data["growth_rate"],
            }
            for name, data in self.species_db.items()
        ]
