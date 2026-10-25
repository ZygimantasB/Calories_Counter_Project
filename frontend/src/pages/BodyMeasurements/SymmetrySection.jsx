import { Card } from '../../components/ui';
import { SYMMETRY_PAIRS, limbImbalance } from './bodyComposition';

// Imbalance thresholds (percent of the average of the two sides)
const BALANCED = 3; // <= 3% considered balanced
const NOTABLE = 5; // > 5% flagged

function badgeFor(pct) {
  if (pct <= BALANCED) return { label: 'balanced', cls: 'bg-green-500/15 text-green-400' };
  if (pct <= NOTABLE) return { label: 'slight', cls: 'bg-yellow-500/15 text-yellow-400' };
  return { label: 'notable', cls: 'bg-amber-500/20 text-amber-400' };
}

export default function SymmetrySection({ latest }) {
  if (!latest) return null;

  const rows = SYMMETRY_PAIRS.map((pair) => ({
    ...pair,
    imb: limbImbalance(latest[pair.left], latest[pair.right]),
  })).filter((r) => r.imb !== null);

  if (rows.length === 0) return null;

  const maxPct = Math.max(...rows.map((r) => r.imb.pct), 1);

  return (
    <Card title="Left / Right Symmetry" subtitle="Based on your latest measurement">
      <div className="space-y-3">
        {rows.map((r) => {
          const { left, right, diff, pct, bigger } = r.imb;
          const badge = badgeFor(pct);
          // Bar width relative to the largest imbalance in the set
          const barWidth = Math.max(4, (pct / maxPct) * 100);
          return (
            <div key={r.base} className="flex items-center gap-3">
              <div className="w-16 text-sm text-gray-300 shrink-0">{r.label}</div>
              <div className="text-xs text-gray-400 w-28 shrink-0 tabular-nums">
                L {left ?? '--'} · R {right ?? '--'}
              </div>
              {/* imbalance bar */}
              <div className="flex-1 h-2 rounded-full bg-gray-700 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    pct <= BALANCED ? 'bg-green-500' : pct <= NOTABLE ? 'bg-yellow-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${barWidth}%` }}
                />
              </div>
              <div className="text-xs text-gray-400 w-24 text-right shrink-0 tabular-nums">
                {diff === 0 ? 'even' : `${bigger === 'right' ? 'R' : 'L'} +${Math.abs(diff)}cm`}
              </div>
              <span className={`text-[11px] px-2 py-0.5 rounded-full shrink-0 ${badge.cls}`}>
                {pct}% · {badge.label}
              </span>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-gray-500 mt-3">
        Imbalance = |L − R| ÷ average. ≤{BALANCED}% balanced, &gt;{NOTABLE}% worth attention.
      </p>
    </Card>
  );
}
