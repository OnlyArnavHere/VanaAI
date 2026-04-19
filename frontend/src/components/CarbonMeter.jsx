/**
 * CarbonMeter — CO₂ sequestration potential display with animated counter.
 */

import { useEffect, useState } from 'react';

export default function CarbonMeter({ co2Potential }) {
  const [animatedValue, setAnimatedValue] = useState(0);
  const targetValue = co2Potential?.per_100_trees_per_year || 0;
  const tenYearValue = co2Potential?.over_10_years || 0;

  useEffect(() => {
    let frame;
    let start = null;
    const duration = 1500;

    const animate = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedValue(+(eased * targetValue).toFixed(2));
      if (progress < 1) {
        frame = requestAnimationFrame(animate);
      }
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [targetValue]);

  return (
    <div className="animate-fade-in-up glass rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🌍</span>
        <h3 className="text-sm font-semibold text-white font-[Outfit]">Carbon Sequestration Potential</h3>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Per year */}
        <div className="relative rounded-xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-forest-600/20 to-forest-900/10" />
          <div className="relative p-4 text-center">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
              Per Year
            </div>
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-3xl font-extrabold font-[Outfit] text-forest-400">
                {animatedValue}
              </span>
              <span className="text-xs text-gray-500">t</span>
            </div>
            <div className="text-[10px] text-gray-500 mt-1">
              CO₂ / 100 trees
            </div>

            {/* Visual bar */}
            <div className="mt-3 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-forest-600 to-forest-400 transition-all duration-1500 ease-out"
                style={{ width: `${Math.min(100, (targetValue / 5) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* 10-year projection */}
        <div className="relative rounded-xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-sky-600/10 to-sky-900/5" />
          <div className="relative p-4 text-center">
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
              10-Year Projection
            </div>
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-3xl font-extrabold font-[Outfit] text-sky-400">
                {tenYearValue.toFixed(1)}
              </span>
              <span className="text-xs text-gray-500">t</span>
            </div>
            <div className="text-[10px] text-gray-500 mt-1">
              total CO₂ captured
            </div>

            {/* Visual bar */}
            <div className="mt-3 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-sky-600 to-sky-400 transition-all duration-1500 ease-out"
                style={{ width: `${Math.min(100, (tenYearValue / 50) * 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Equivalent metric */}
      <div className="mt-4 flex items-center gap-3 rounded-xl bg-white/[0.03] p-3">
        <span className="text-lg">🚗</span>
        <div>
          <div className="text-xs text-gray-400">
            Equivalent to taking <span className="font-bold text-forest-400">{Math.round(tenYearValue * 4.6)}</span> cars off the road for a year
          </div>
          <div className="text-[10px] text-gray-600 mt-0.5">
            Based on avg. 4.6 tonnes CO₂ per passenger vehicle per year
          </div>
        </div>
      </div>
    </div>
  );
}
