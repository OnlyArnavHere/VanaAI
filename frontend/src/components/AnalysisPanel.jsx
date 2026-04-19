/**
 * AnalysisPanel — Slide-in panel displaying all analysis results.
 * Shows data progressively: fitness score → species → CO₂ → AI rationale.
 */

import { useState, useEffect } from 'react';
import FitnessScore from './FitnessScore';
import SpeciesCard from './SpeciesCard';
import CarbonMeter from './CarbonMeter';

export default function AnalysisPanel({ result, onClose }) {
  const [showSpecies, setShowSpecies] = useState(false);
  const [showCarbon, setShowCarbon] = useState(false);
  const [showRationale, setShowRationale] = useState(false);
  const [displayedRationale, setDisplayedRationale] = useState('');

  // Progressive reveal timing
  useEffect(() => {
    if (!result) return;

    const t1 = setTimeout(() => setShowSpecies(true), 600);
    const t2 = setTimeout(() => setShowCarbon(true), 1200);
    const t3 = setTimeout(() => setShowRationale(true), 1800);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [result]);

  // Typewriter effect for AI rationale
  useEffect(() => {
    if (!showRationale || !result?.ai_rationale) return;

    const text = result.ai_rationale;
    let index = 0;
    setDisplayedRationale('');

    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedRationale(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 12);

    return () => clearInterval(interval);
  }, [showRationale, result?.ai_rationale]);

  if (!result) return null;

  return (
    <div className="absolute top-0 right-0 z-30 h-full w-full max-w-md animate-slide-in">
      <div className="h-full glass-strong rounded-l-3xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 px-6 pt-5 pb-4 border-b border-white/5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold font-[Outfit] text-white">Zone Analysis</h2>
              <p className="text-[11px] text-gray-500 mt-0.5">
                ID: {result.zone_id?.slice(0, 8)}…
              </p>
            </div>
            <button
              onClick={onClose}
              className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-400 hover:text-white transition-all duration-200 hover:scale-105"
              aria-label="Close analysis panel"
              id="close-analysis-panel"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {/* Fitness Score */}
          <section>
            <FitnessScore
              score={result.fitness_score}
              breakdown={result.fitness_breakdown}
            />
          </section>

          {/* Constraints */}
          {result.constraints_detected?.length > 0 && (
            <section className="animate-fade-in-up">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm">🚧</span>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Detected Constraints
                </h3>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {result.constraints_detected.map((c, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-amber-900/30 text-amber-400 border border-amber-700/20"
                  >
                    {c.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* Species Recommendations */}
          {showSpecies && result.species_recommendations && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm">🌿</span>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Recommended Species
                </h3>
              </div>
              <div className="space-y-3">
                {result.species_recommendations.map((sp, i) => (
                  <div key={sp.species} className="animate-fade-in-up" style={{ animationDelay: `${i * 150}ms` }}>
                    <SpeciesCard species={sp} index={i} />
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Carbon Meter */}
          {showCarbon && result.total_co2_potential && (
            <section>
              <CarbonMeter co2Potential={result.total_co2_potential} />
            </section>
          )}

          {/* AI Rationale */}
          {showRationale && (
            <section className="animate-fade-in-up">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm">🤖</span>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  AI Analysis
                </h3>
              </div>
              <div className="glass rounded-2xl p-4">
                <p className="text-sm text-gray-300 leading-relaxed">
                  {displayedRationale}
                  {displayedRationale.length < (result.ai_rationale?.length || 0) && (
                    <span className="inline-block w-0.5 h-4 bg-forest-400 ml-0.5 animate-pulse" />
                  )}
                </p>
              </div>
            </section>
          )}

          {/* Bottom Spacer */}
          <div className="h-4" />
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 px-6 py-3 border-t border-white/5 bg-surface-100/50">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-600">
              Powered by NASA POWER · SoilGrids · Sentinel-2 · OSM
            </span>
            <button
              onClick={() => {
                const dataStr = JSON.stringify(result, null, 2);
                const blob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `vanai-analysis-${result.zone_id?.slice(0, 8)}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="text-[10px] text-forest-500 hover:text-forest-400 font-medium transition-colors"
              id="export-analysis-btn"
            >
              Export JSON ↗
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
