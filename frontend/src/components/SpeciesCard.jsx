/**
 * SpeciesCard — Displays a recommended tree species with survival probabilities.
 */

import { getScoreColor } from '../utils/mapLayers';

export default function SpeciesCard({ species, index }) {
  const {
    common_name,
    species: scientificName,
    survival_1yr,
    survival_5yr,
    co2_tonnes_per_year,
    suitability_reasons = [],
    constraints = [],
  } = species;

  // Medal colors for top 3
  const medals = ['🥇', '🥈', '🥉'];
  const medal = medals[index] || '';

  const s1Color = getScoreColor(survival_1yr * 100);
  const s5Color = getScoreColor(survival_5yr * 100);

  // Species emoji mapping
  const speciesEmojis = {
    Neem: '🌿',
    Banyan: '🌳',
    Peepal: '🍃',
    Mango: '🥭',
    Teak: '🪵',
    Bamboo: '🎋',
    Eucalyptus: '🌲',
    Coconut: '🥥',
    Shisham: '🌴',
    Arjuna: '🌱',
  };
  const emoji = speciesEmojis[common_name] || '🌳';

  return (
    <div
      className="group relative rounded-2xl overflow-hidden transition-all duration-300 hover:scale-[1.02]"
      style={{
        animationDelay: `${index * 150}ms`,
        animationFillMode: 'both',
      }}
    >
      {/* Gradient border effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-forest-500/20 via-transparent to-forest-700/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="relative glass rounded-2xl p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-forest-800/80 to-forest-950/80 flex items-center justify-center text-2xl flex-shrink-0 shadow-lg">
            {emoji}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white truncate">{common_name}</h3>
              <span className="text-base">{medal}</span>
            </div>
            <p className="text-[11px] text-gray-500 italic truncate">{scientificName}</p>
          </div>
          {/* CO₂ badge */}
          <div className="flex-shrink-0 text-right">
            <div className="text-[10px] text-gray-500 uppercase tracking-wide">CO₂/yr</div>
            <div className="text-sm font-bold text-forest-400">
              {(co2_tonnes_per_year * 1000).toFixed(0)}
              <span className="text-[9px] text-gray-500 ml-0.5">kg</span>
            </div>
          </div>
        </div>

        {/* Survival Gauges */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <SurvivalGauge label="1-Year Survival" value={survival_1yr} color={s1Color} />
          <SurvivalGauge label="5-Year Survival" value={survival_5yr} color={s5Color} />
        </div>

        {/* Suitability Tags */}
        {suitability_reasons.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {suitability_reasons.map((reason, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-forest-900/50 text-forest-300 border border-forest-700/30"
              >
                {reason}
              </span>
            ))}
          </div>
        )}

        {/* Constraint Warnings */}
        {constraints.length > 0 && (
          <div className="mt-2 space-y-1">
            {constraints.map((constraint, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 text-[10px] text-amber-400/80"
              >
                <span>⚠️</span>
                <span>{constraint}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Mini survival probability gauge.
 */
function SurvivalGauge({ label, value, color }) {
  const pct = Math.round(value * 100);

  return (
    <div className="rounded-xl bg-white/[0.03] p-2.5">
      <div className="text-[9px] uppercase tracking-wider text-gray-500 mb-1.5">{label}</div>
      <div className="flex items-end gap-1.5">
        <span className="text-lg font-bold" style={{ color }}>{pct}</span>
        <span className="text-[10px] text-gray-500 mb-0.5">%</span>
      </div>
      <div className="h-1 rounded-full bg-white/5 mt-1.5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}80, ${color})`,
            boxShadow: `0 0 6px ${color}30`,
          }}
        />
      </div>
    </div>
  );
}
