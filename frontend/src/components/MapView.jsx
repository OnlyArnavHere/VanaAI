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
  const [plants, setPlants] = useState([]);
  const [selectedPlant, setSelectedPlant] = useState("");
  const [bestLocations, setBestLocations] = useState([]);
  const dynamicMarkersRef = useRef([]);

  // Fetch species list on mount
  useEffect(() => {
    fetch('http://localhost:8000/api/species')
      .then(res => res.json())
      .then(data => {
         if (data.species) setPlants(data.species);
      })
      .catch(err => console.error("Could not load species list", err));
  }, []);

  const handlePlantSelect = async (e) => {
    const species = e.target.value;
    setSelectedPlant(species);
    if (!species) {
      setBestLocations([]);
      return;
    }
    
    try {
      const res = await fetch(`http://localhost:8000/api/species/${encodeURIComponent(species)}/best-locations`);
      if (res.ok) {
        const data = await res.json();
        setBestLocations(data);
        if (data.length > 0 && mapRef.current) {
          mapRef.current.flyTo({ center: [data[0].lon, data[0].lat], zoom: 5, duration: 2000 });
        }
      }
    } catch(err) {
      console.error(err);
    }
  };

  // Render best location markers
  useEffect(() => {
    if (!mapRef.current) return;
    
    // remove old markers
    dynamicMarkersRef.current.forEach(m => m.remove());
    dynamicMarkersRef.current = [];

    bestLocations.forEach(loc => {
      const el = document.createElement('div');
      el.className = 'best-location-marker';
      el.style.cssText = `
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #10b981;
        border: 2px solid #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        box-shadow: 0 0 15px rgba(16,185,129,0.8);
        cursor: pointer;
      `;
      el.innerHTML = '🌿';

      const popup = new maplibregl.Popup({ offset: 18 })
        .setHTML(`
          <div style="text-align:center;color:#333;font-family:'Inter',sans-serif;">
            <div style="font-weight:800;font-size:14px;margin-bottom:2px;">${loc.name}</div>
            <div style="font-size:12px;font-weight:600;color:#10b981;">Match Score: ${loc.score}%</div>
            <div style="font-size:11px;opacity:0.8;">1-yr Survival: ${loc.survival_prob}%</div>
          </div>
        `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([loc.lon, loc.lat])
        .setPopup(popup)
        .addTo(mapRef.current);
        
      el.addEventListener('mouseenter', () => popup.addTo(mapRef.current));
      el.addEventListener('mouseleave', () => popup.remove());
      el.addEventListener('click', () => {
        if (onLocationClick) onLocationClick(loc.lat, loc.lon);
      });
        
      dynamicMarkersRef.current.push(marker);
    });
  }, [bestLocations, onLocationClick]);

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

    // Removed click handler to fix navigation issues. Users now use the target button.
    
    // Cursor
    map.getCanvas().style.cursor = 'grab';

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

      {/* Logo / Title overlay with Plant Selector */}
      <div className="absolute top-5 left-5 z-10 flex flex-col gap-3">
        <div className="glass rounded-2xl px-5 py-3 flex items-center gap-3 shadow-2xl">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-forest-400 to-forest-600 flex items-center justify-center text-xl shadow-inner">
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
        
        <div className="glass rounded-xl px-4 py-3 shadow-xl animate-fade-in-up">
          <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
            Find best locations for
          </label>
          <select 
            className="w-full bg-surface-300/50 text-sm text-white rounded-lg px-3 py-2 border border-white/10 outline-none focus:border-forest-400 transition-colors"
            value={selectedPlant}
            onChange={handlePlantSelect}
          >
            <option value="">Select a plant species...</option>
            {plants.map(p => (
              <option key={p.species} value={p.species}>{p.common_name} ({p.species})</option>
            ))}
          </select>
        </div>
      </div>

      {/* Coordinate display */}
      {selectedLocation && (
        <div className="absolute bottom-8 left-5 z-10 animate-fade-in-up">
          <div className="glass rounded-xl px-4 py-2 text-xs text-gray-300 font-mono shadow-lg">
            📍 {selectedLocation.latitude.toFixed(4)}°N, {selectedLocation.longitude.toFixed(4)}°E
          </div>
        </div>
      )}

      {/* Center Target Crosshair */}
      {!selectedLocation && !isLoading && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 pointer-events-none drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">
           <svg className="w-8 h-8 text-white opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
             <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v4m0 8v4m-8-8h4m8 0h4m-4 0a4 4 0 11-8 0 4 4 0 018 0z" />
           </svg>
        </div>
      )}

      {/* Analyze Target Button */}
      {!selectedLocation && !isLoading && (
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-10 animate-slide-in">
          <button 
            onClick={() => {
              if (mapRef.current && onLocationClick) {
                const center = mapRef.current.getCenter();
                onLocationClick(center.lat, center.lng);
              }
            }}
            className="group relative flex items-center gap-3 px-8 py-3.5 rounded-full bg-forest-600 hover:bg-forest-500 text-white font-medium shadow-[0_0_30px_rgba(34,197,94,0.3)] hover:shadow-[0_0_40px_rgba(34,197,94,0.5)] transition-all transform hover:scale-105 border border-forest-400/30 overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            <span className="text-lg">🎯</span>
            <span className="tracking-wide">Analyze Target Location</span>
          </button>
        </div>
      )}
    </div>
  );
}
