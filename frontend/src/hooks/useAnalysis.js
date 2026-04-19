/**
 * useAnalysis hook — manages the analysis API call, state, and loading.
 */

import { useState, useCallback } from 'react';

const API_BASE = '/api';

export function useAnalysis() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);

  const analyze = useCallback(async (latitude, longitude, radiusMeters = 500) => {
    setIsLoading(true);
    setError(null);
    setSelectedLocation({ latitude, longitude });

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude,
          longitude,
          radius_meters: radiusMeters,
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysisResult(data);
      return data;
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message);
      
      // Return mock data for demo/development when backend is down
      const mockData = generateMockAnalysis(latitude, longitude);
      setAnalysisResult(mockData);
      return mockData;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearAnalysis = useCallback(() => {
    setAnalysisResult(null);
    setError(null);
    setSelectedLocation(null);
  }, []);

  return {
    analysisResult,
    isLoading,
    error,
    selectedLocation,
    analyze,
    clearAnalysis,
  };
}

/**
 * Generate mock analysis data for development and when the backend is unavailable.
 */
function generateMockAnalysis(lat, lon) {
  // Use lat/lon to produce consistent but varied results
  const seed = Math.abs(Math.sin(lat * 12.9898 + lon * 78.233) * 43758.5453) % 1;
  const fitness = Math.round(35 + seed * 55); // 35–90 range

  const soilScore = Math.round(40 + seed * 50);
  const climateScore = Math.round(50 + seed * 45);
  const vegScore = Math.round(30 + seed * 60);
  const landScore = Math.round(45 + seed * 50);
  const constScore = Math.round(60 + seed * 40);

  const species = [
    {
      species: 'Azadirachta indica',
      common_name: 'Neem',
      survival_1yr: +(0.72 + seed * 0.2).toFixed(2),
      survival_5yr: +(0.55 + seed * 0.2).toFixed(2),
      co2_tonnes_per_year: 0.023,
      suitability_reasons: ['drought tolerant', 'native to region', 'poor soil tolerant'],
      constraints: [],
    },
    {
      species: 'Ficus religiosa',
      common_name: 'Peepal',
      survival_1yr: +(0.68 + seed * 0.2).toFixed(2),
      survival_5yr: +(0.50 + seed * 0.2).toFixed(2),
      co2_tonnes_per_year: 0.030,
      suitability_reasons: ['high O₂ output', 'sacred tree', 'long-lived'],
      constraints: [],
    },
    {
      species: 'Bambusa vulgaris',
      common_name: 'Bamboo',
      survival_1yr: +(0.75 + seed * 0.18).toFixed(2),
      survival_5yr: +(0.60 + seed * 0.2).toFixed(2),
      co2_tonnes_per_year: 0.040,
      suitability_reasons: ['fastest growing', 'high CO₂ capture', 'erosion control'],
      constraints: seed < 0.3 ? ['insufficient rainfall'] : [],
    },
  ];

  // Create circular GeoJSON polygon
  const numPoints = 32;
  const delta = 500 / 111320;
  const ring = [];
  for (let i = 0; i < numPoints; i++) {
    const angle = (2 * Math.PI * i) / numPoints;
    ring.push([
      +(lon + delta * Math.sin(angle) / Math.cos(lat * Math.PI / 180)).toFixed(6),
      +(lat + delta * Math.cos(angle)).toFixed(6),
    ]);
  }
  ring.push(ring[0]);

  const color = fitness >= 70 ? '#22c55e' : fitness >= 40 ? '#eab308' : '#ef4444';

  return {
    zone_id: crypto.randomUUID?.() || 'mock-' + Date.now(),
    fitness_score: fitness,
    fitness_breakdown: {
      soil_score: soilScore,
      climate_score: climateScore,
      vegetation_score: vegScore,
      land_use_score: landScore,
      constraints_score: constScore,
    },
    species_recommendations: species,
    total_co2_potential: {
      per_100_trees_per_year: +(species.reduce((a, s) => a + s.co2_tonnes_per_year, 0) * 100 / species.length).toFixed(2),
      over_10_years: +(species.reduce((a, s) => a + s.co2_tonnes_per_year, 0) * 1000 / species.length).toFixed(2),
    },
    constraints_detected: seed > 0.6 ? ['road_80m_north', 'building_cluster_east'] : ['open_land'],
    planting_zones: {
      type: 'FeatureCollection',
      features: [{
        type: 'Feature',
        geometry: { type: 'Polygon', coordinates: [ring] },
        properties: { fitness_score: fitness, color, category: fitness >= 70 ? 'high' : fitness >= 40 ? 'medium' : 'low', radius_m: 500 },
      }],
    },
    ai_rationale: `This zone at ${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E scores ${fitness}/100 for afforestation potential. The soil analysis indicates a pH of ${(5.5 + seed * 2.5).toFixed(1)}, which is ${seed > 0.5 ? 'within the optimal range' : 'slightly outside the ideal range'} for most native species. With an estimated ${(500 + seed * 1000).toFixed(0)}mm of annual rainfall, ${seed > 0.4 ? 'most drought-tolerant species will thrive' : 'irrigation support may be needed for the first year'}. Satellite imagery shows ${seed < 0.3 ? 'bare land — an excellent opportunity for new planting' : seed < 0.6 ? 'sparse vegetation that can benefit from enrichment planting' : 'moderate existing canopy'}. We recommend Neem as the primary species given its exceptional adaptability to local conditions, combined with Peepal for biodiversity and Bamboo for rapid carbon capture.`,
  };
}
