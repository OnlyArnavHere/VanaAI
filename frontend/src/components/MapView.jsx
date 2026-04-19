/**
 * MapView — Full-screen MapLibre GL map with click-to-analyze interaction.
 */

import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  MAP_STYLE,
  addAnalysisZoneLayer,
  updateAnalysisZone,
  CITY_SCORES,
  getScoreColor,
} from '../utils/mapLayers';

export default function MapView({ onLocationClick, analysisResult, isLoading, selectedLocation }) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const pulseRef = useRef(null);
  const [mapReady, setMapReady] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(true);

  // Initialize the map
  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [78.9629, 20.5937], // India center
      zoom: 5,
      minZoom: 3,
      maxZoom: 18,
      attributionControl: true,
    });

    map.addControl(new maplibregl.NavigationControl(), 'bottom-right');

    map.on('load', () => {
      addAnalysisZoneLayer(map);
      addCityMarkers(map);
      setMapReady(true);
    });

    // Click handler
    map.on('click', (e) => {
      const { lng, lat } = e.lngLat;
      if (onLocationClick) {
        onLocationClick(lat, lng);
      }
    });

    // Cursor
    map.getCanvas().style.cursor = 'crosshair';

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Add city score markers
  function addCityMarkers(map) {
    CITY_SCORES.forEach((city) => {
      const el = document.createElement('div');
      el.className = 'city-marker';
      el.style.cssText = `
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: ${getScoreColor(city.score)};
        border: 2px solid rgba(255,255,255,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        font-weight: 700;
        color: #000;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 12px ${getScoreColor(city.score)}40;
        font-family: 'Inter', sans-serif;
      `;
      el.textContent = city.score;

      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.3)';
        el.style.zIndex = '10';
      });
      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)';
        el.style.zIndex = '1';
      });
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        map.flyTo({ center: [city.lon, city.lat], zoom: 12, duration: 1500 });
        setTimeout(() => {
          if (onLocationClick) onLocationClick(city.lat, city.lon);
        }, 800);
      });

      const popup = new maplibregl.Popup({ offset: 18, closeButton: false, closeOnClick: false })
        .setHTML(`
          <div style="text-align:center;">
            <div style="font-weight:700;font-size:13px;margin-bottom:2px;">${city.name}</div>
            <div style="font-size:11px;opacity:0.7;">Fitness: <span style="color:${getScoreColor(city.score)};font-weight:600;">${city.score}/100</span></div>
            <div style="font-size:10px;opacity:0.5;margin-top:2px;">Click to analyze</div>
          </div>
        `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([city.lon, city.lat])
        .setPopup(popup)
        .addTo(map);

      el.addEventListener('mouseenter', () => popup.addTo(map));
      el.addEventListener('mouseleave', () => popup.remove());
    });
  }

  // Update analysis zone when results change
  useEffect(() => {
    if (!mapRef.current || !mapReady) return;
    if (analysisResult?.planting_zones) {
      updateAnalysisZone(mapRef.current, analysisResult.planting_zones);
    }
  }, [analysisResult, mapReady]);

  // Pulse marker during loading
  useEffect(() => {
    if (!mapRef.current || !selectedLocation) return;

    // Remove old marker
    if (markerRef.current) {
      markerRef.current.remove();
      markerRef.current = null;
    }
    if (pulseRef.current) {
      pulseRef.current.remove();
      pulseRef.current = null;
    }

    const { latitude, longitude } = selectedLocation;

    // Fly to location
    mapRef.current.flyTo({
      center: [longitude, latitude],
      zoom: 14,
      duration: 1200,
    });

    // Create pulsing marker
    const el = document.createElement('div');
    el.style.cssText = `
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #22c55e;
      border: 3px solid #fff;
      box-shadow: 0 0 20px rgba(34,197,94,0.6);
      position: relative;
    `;

    if (isLoading) {
      const pulse = document.createElement('div');
      pulse.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: rgba(34,197,94,0.4);
        transform: translate(-50%, -50%);
        animation: pulse-ring 1.5s ease-out infinite;
      `;
      el.appendChild(pulse);

      const pulse2 = document.createElement('div');
      pulse2.style.cssText = pulse.style.cssText;
      pulse2.style.animationDelay = '0.5s';
      el.appendChild(pulse2);
    }

    markerRef.current = new maplibregl.Marker({ element: el })
      .setLngLat([longitude, latitude])
      .addTo(mapRef.current);

  }, [selectedLocation, isLoading]);

  // Update marker appearance when loading finishes
  useEffect(() => {
    if (!markerRef.current || !analysisResult) return;

    const el = markerRef.current.getElement();
    const color = getScoreColor(analysisResult.fitness_score);
    el.style.background = color;
    el.style.boxShadow = `0 0 20px ${color}60`;

    // Remove pulse animations
    const pulses = el.querySelectorAll('div');
    pulses.forEach(p => p.remove());
  }, [analysisResult]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Logo / Title overlay */}
      <div className="absolute top-5 left-5 z-10">
        <div className="glass rounded-2xl px-5 py-3 flex items-center gap-3 shadow-2xl">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-forest-400 to-forest-600 flex items-center justify-center text-xl">
            🌳
          </div>
          <div>
            <h1 className="text-lg font-bold font-[Outfit] tracking-tight text-white">
              Vana<span className="text-forest-400">AI</span>
            </h1>
            <p className="text-[10px] text-gray-400 -mt-0.5 tracking-wide uppercase">
              Afforestation Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Coordinate display */}
      {selectedLocation && (
        <div className="absolute bottom-8 left-5 z-10 animate-fade-in-up">
          <div className="glass rounded-xl px-4 py-2 text-xs text-gray-300 font-mono">
            📍 {selectedLocation.latitude.toFixed(4)}°N, {selectedLocation.longitude.toFixed(4)}°E
          </div>
        </div>
      )}

      {/* Instruction hint */}
      {!selectedLocation && !isLoading && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 animate-float">
          <div className="glass rounded-full px-6 py-3 text-sm text-gray-300 flex items-center gap-2 shadow-2xl">
            <span className="w-2 h-2 rounded-full bg-forest-400 animate-pulse" />
            Click anywhere on the map to analyze afforestation potential
          </div>
        </div>
      )}
    </div>
  );
}
