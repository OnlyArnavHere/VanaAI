/**
 * MapLibre layer definitions for VanaAI.
 * Handles analyzed zone polygons, markers, and heatmap layers.
 */

export const ANALYSIS_ZONE_SOURCE = 'analysis-zone';
export const ANALYSIS_ZONE_LAYER = 'analysis-zone-fill';
export const ANALYSIS_ZONE_OUTLINE = 'analysis-zone-outline';
export const PULSE_MARKER_SOURCE = 'pulse-marker';

/**
 * Add the analysis zone GeoJSON layer to the map.
 */
export function addAnalysisZoneLayer(map) {
  if (map.getSource(ANALYSIS_ZONE_SOURCE)) {
    map.removeLayer(ANALYSIS_ZONE_OUTLINE);
    map.removeLayer(ANALYSIS_ZONE_LAYER);
    map.removeSource(ANALYSIS_ZONE_SOURCE);
  }

  map.addSource(ANALYSIS_ZONE_SOURCE, {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });

  map.addLayer({
    id: ANALYSIS_ZONE_LAYER,
    type: 'fill',
    source: ANALYSIS_ZONE_SOURCE,
    paint: {
      'fill-color': ['get', 'color'],
      'fill-opacity': 0.25,
    },
  });

  map.addLayer({
    id: ANALYSIS_ZONE_OUTLINE,
    type: 'line',
    source: ANALYSIS_ZONE_SOURCE,
    paint: {
      'line-color': ['get', 'color'],
      'line-width': 2.5,
      'line-opacity': 0.8,
      'line-dasharray': [2, 1],
    },
  });
}

/**
 * Update the analysis zone with new GeoJSON data.
 */
export function updateAnalysisZone(map, geojson) {
  const source = map.getSource(ANALYSIS_ZONE_SOURCE);
  if (source) {
    source.setData(geojson);
  }
}

/**
 * Get the score-based color for visual feedback.
 */
export function getScoreColor(score) {
  if (score >= 70) return '#22c55e';
  if (score >= 40) return '#eab308';
  return '#ef4444';
}

/**
 * Get a human-readable label for the score.
 */
export function getScoreLabel(score) {
  if (score >= 80) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 50) return 'Moderate';
  if (score >= 30) return 'Fair';
  return 'Poor';
}

/**
 * OSM dark tile style for MapLibre (CartoDB dark matter).
 */
export const MAP_STYLE = {
  version: 8,
  name: 'VanaAI Dark',
  sources: {
    'osm-tiles': {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
        'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
        'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
      ],
      tileSize: 256,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    },
  },
  layers: [
    {
      id: 'osm-tiles-layer',
      type: 'raster',
      source: 'osm-tiles',
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

/**
 * Pre-computed mock scores for major Indian cities (heatmap mode).
 */
export const CITY_SCORES = [
  { name: 'Delhi', lat: 28.6139, lon: 77.2090, score: 42 },
  { name: 'Mumbai', lat: 19.0760, lon: 72.8777, score: 55 },
  { name: 'Bangalore', lat: 12.9716, lon: 77.5946, score: 68 },
  { name: 'Chennai', lat: 13.0827, lon: 80.2707, score: 61 },
  { name: 'Kolkata', lat: 22.5726, lon: 88.3639, score: 48 },
  { name: 'Hyderabad', lat: 17.3850, lon: 78.4867, score: 65 },
  { name: 'Pune', lat: 18.5204, lon: 73.8567, score: 72 },
  { name: 'Jaipur', lat: 26.9124, lon: 75.7873, score: 38 },
  { name: 'Lucknow', lat: 26.8467, lon: 80.9462, score: 52 },
  { name: 'Ahmedabad', lat: 23.0225, lon: 72.5714, score: 45 },
  { name: 'Bhopal', lat: 23.2599, lon: 77.4126, score: 63 },
  { name: 'Dehradun', lat: 30.3165, lon: 78.0322, score: 78 },
  { name: 'Coimbatore', lat: 11.0168, lon: 76.9558, score: 75 },
  { name: 'Guwahati', lat: 26.1445, lon: 91.7362, score: 82 },
  { name: 'Shimla', lat: 31.1048, lon: 77.1734, score: 80 },
  { name: 'Kochi', lat: 9.9312, lon: 76.2673, score: 70 },
  { name: 'Nagpur', lat: 21.1458, lon: 79.0882, score: 58 },
  { name: 'Chandigarh', lat: 30.7333, lon: 76.7794, score: 60 },
  { name: 'Mysore', lat: 12.2958, lon: 76.6394, score: 71 },
  { name: 'Gangtok', lat: 27.3389, lon: 88.6065, score: 85 },
];
