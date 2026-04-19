/**
 * FitnessScore — Animated SVG ring displaying the 0-100 ecological fitness score.
 */

import { useEffect, useState } from 'react';
import { getScoreColor, getScoreLabel } from '../utils/mapLayers';

export default function FitnessScore({ score, breakdown }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const circumference = 2 * Math.PI * 45; // radius=45
  const offset = circumference - (animatedScore / 100) * circumference;
  const color = getScoreColor(score);
  const label = getScoreLabel(score);

  // Animate score counting
  useEffect(() => {
    let frame;
    let start = null;
    const duration = 1200;

    const animate = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(eased * score));
      if (progress < 1) {
        frame = requestAnimationFrame(animate);
      }
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const breakdownItems = [
    { key: 'soil_score', label: 'Soil', icon: '🪨', color: '#a16207' },
    { key: 'climate_score', label: 'Climate', icon: '🌤️', color: '#0ea5e9' },
    { key: 'vegetation_score', label: 'Vegetation', icon: '🌿', color: '#22c55e' },
    { key: 'land_use_score', label: 'Land Use', icon: '🏗️', color: '#8b5cf6' },
    { key: 'constraints_score', label: 'Constraints', icon: '⚠️', color: '#f59e0b' },
  ];

  return (
    <div className="animate-fade-in-up">
      {/* Main Score Ring */}
      <div className="flex items-center gap-6 mb-5">
        <div className="relative w-28 h-28 flex-shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            {/* Background ring */}
            <circle
              cx="50" cy="50" r="45"
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="8"
            />
            {/* Score ring */}
            <circle
              cx="50" cy="50" r="45"
              fill="none"
              stroke={color}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{
                transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)',
                filter: `drop-shadow(0 0 8px ${color}60)`,
              }}
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-extrabold font-[Outfit]" style={{ color }}>
              {animatedScore}
            </span>
            <span className="text-[9px] uppercase tracking-widest text-gray-500 mt-0.5">
              / 100
            </span>
          </div>
        </div>

        <div>
          <div className="text-sm font-medium text-gray-400 mb-1">Ecological Fitness</div>
          <div className="text-2xl font-bold font-[Outfit]" style={{ color }}>
            {label}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Composite score from 5 ecological factors
          </p>
        </div>
      </div>

      {/* Breakdown Bars */}
      {breakdown && (
        <div className="space-y-2.5">
          {breakdownItems.map(({ key, label, icon, color: barColor }) => {
            const value = breakdown[key] || 0;
            return (
              <div key={key} className="group">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <span>{icon}</span>
                    <span>{label}</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-300">{Math.round(value)}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-1000 ease-out"
                    style={{
                      width: `${value}%`,
                      background: `linear-gradient(90deg, ${barColor}80, ${barColor})`,
                      boxShadow: `0 0 8px ${barColor}40`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
