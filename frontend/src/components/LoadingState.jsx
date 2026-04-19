/**
 * LoadingState — Analysis-in-progress animation with progress steps.
 */

import { useState, useEffect } from 'react';

const ANALYSIS_STEPS = [
  { id: 'satellite', label: 'Fetching satellite imagery', icon: '🛰️', duration: 1200 },
  { id: 'climate', label: 'Querying climate data', icon: '🌤️', duration: 800 },
  { id: 'soil', label: 'Analyzing soil composition', icon: '🪨', duration: 1000 },
  { id: 'landuse', label: 'Scanning land use patterns', icon: '🗺️', duration: 900 },
  { id: 'species', label: 'Matching tree species', icon: '🌳', duration: 700 },
  { id: 'scoring', label: 'Computing fitness score', icon: '📊', duration: 600 },
  { id: 'ai', label: 'Generating AI rationale', icon: '🤖', duration: 1500 },
];

export default function LoadingState({ isLoading }) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      setActiveStep(0);
      return;
    }

    let timeout;
    let step = 0;

    const advanceStep = () => {
      if (step < ANALYSIS_STEPS.length - 1) {
        step += 1;
        setActiveStep(step);
        timeout = setTimeout(advanceStep, ANALYSIS_STEPS[step].duration);
      }
    };

    timeout = setTimeout(advanceStep, ANALYSIS_STEPS[0].duration);
    return () => clearTimeout(timeout);
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center pointer-events-none">
      <div className="glass-strong rounded-3xl p-8 max-w-sm w-full mx-4 shadow-2xl pointer-events-auto animate-fade-in-up">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="relative w-10 h-10">
            <div className="absolute inset-0 rounded-xl bg-forest-500/20 animate-pulse" />
            <div className="relative w-full h-full rounded-xl bg-gradient-to-br from-forest-400 to-forest-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          </div>
          <div>
            <h3 className="text-base font-bold text-white font-[Outfit]">Analyzing Zone</h3>
            <p className="text-xs text-gray-500">Processing ecological data…</p>
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-2">
          {ANALYSIS_STEPS.map((step, i) => {
            const isActive = i === activeStep;
            const isDone = i < activeStep;

            return (
              <div
                key={step.id}
                className={`flex items-center gap-3 rounded-xl px-3 py-2 transition-all duration-300 ${
                  isActive
                    ? 'bg-forest-900/40 border border-forest-600/30'
                    : isDone
                    ? 'opacity-60'
                    : 'opacity-25'
                }`}
              >
                <span className="text-base w-6 text-center flex-shrink-0">
                  {isDone ? '✅' : step.icon}
                </span>
                <span className={`text-xs flex-1 ${isActive ? 'text-forest-300 font-medium' : 'text-gray-400'}`}>
                  {step.label}
                </span>
                {isActive && (
                  <div className="flex gap-0.5">
                    <span className="w-1 h-1 rounded-full bg-forest-400" style={{ animation: 'typing 1s ease-in-out infinite' }} />
                    <span className="w-1 h-1 rounded-full bg-forest-400" style={{ animation: 'typing 1s ease-in-out 0.2s infinite' }} />
                    <span className="w-1 h-1 rounded-full bg-forest-400" style={{ animation: 'typing 1s ease-in-out 0.4s infinite' }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="mt-5 h-1 rounded-full bg-white/5 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-forest-600 to-forest-400 transition-all duration-500 ease-out"
            style={{ width: `${((activeStep + 1) / ANALYSIS_STEPS.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
