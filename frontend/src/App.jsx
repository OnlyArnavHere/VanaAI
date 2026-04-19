/**
 * VanaAI — Root Application Component.
 *
 * Orchestrates the MapView, AnalysisPanel, and LoadingState.
 */

import { useCallback } from 'react';
import MapView from './components/MapView';
import AnalysisPanel from './components/AnalysisPanel';
import LoadingState from './components/LoadingState';
import { useAnalysis } from './hooks/useAnalysis';

export default function App() {
  const {
    analysisResult,
    isLoading,
    error,
    selectedLocation,
    analyze,
    clearAnalysis,
  } = useAnalysis();

  const handleLocationClick = useCallback(
    (lat, lng) => {
      if (isLoading) return; // Prevent double-clicks
      analyze(lat, lng, 500);
    },
    [analyze, isLoading]
  );

  const handleClose = useCallback(() => {
    clearAnalysis();
  }, [clearAnalysis]);

  return (
    <div className="relative w-full h-full">
      {/* Full-screen Map */}
      <MapView
        onLocationClick={handleLocationClick}
        analysisResult={analysisResult}
        isLoading={isLoading}
        selectedLocation={selectedLocation}
      />

      {/* Loading Overlay */}
      <LoadingState isLoading={isLoading} />

      {/* Results Panel */}
      {analysisResult && !isLoading && (
        <AnalysisPanel result={analysisResult} onClose={handleClose} />
      )}

      {/* Error Toast */}
      {error && !isLoading && (
        <div className="absolute top-5 right-5 z-50 animate-fade-in-up">
          <div className="glass rounded-xl px-4 py-3 flex items-center gap-3 max-w-xs shadow-xl border border-amber-600/20">
            <span className="text-amber-400 text-sm">⚠️</span>
            <div>
              <p className="text-xs text-amber-300 font-medium">Using demo data</p>
              <p className="text-[10px] text-gray-500 mt-0.5">Backend unavailable — showing mock results</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
