import { TrendingDown, TrendingUp, Minus, Info } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { Card } from '../../components/ui';
import { navyBodyFat, waistToHip, waistToHeight } from './bodyComposition';

// belly = waist, butt = hip
function bodyFatFor(m, settings) {
  if (!m || !settings) return null;
  return navyBodyFat({
    gender: settings.gender,
    height: settings.height,
    neck: m.neck,
    waist: m.belly,
    hip: m.butt,
  });
}

function DeltaBadge({ delta, lowerIsBetter = true, unit = '' }) {
  if (delta === null || delta === undefined || delta === 0) {
    return (
      <span className="flex items-center gap-1 text-xs text-gray-400">
        <Minus className="w-3 h-3" /> no change
      </span>
    );
  }
  const good = lowerIsBetter ? delta < 0 : delta > 0;
  const color = good ? 'text-green-400' : 'text-red-400';
  const Icon = delta < 0 ? TrendingDown : TrendingUp;
  return (
    <span className={`flex items-center gap-1 text-xs ${color}`}>
      <Icon className="w-3 h-3" />
      {delta > 0 ? '+' : ''}
      {delta}
      {unit}
    </span>
  );
}

export default function BodyCompositionCards({ measurements, settings }) {
  // measurements are newest-first
  const latest = measurements[0] || null;
  const previous = measurements[1] || null;
  if (!latest) return null;

  const missingProfile = !settings?.height || !settings?.gender;

  const bfLatest = bodyFatFor(latest, settings);
  const bfPrev = bodyFatFor(previous, settings);
  const bfDelta = bfLatest !== null && bfPrev !== null
    ? Math.round((bfLatest - bfPrev) * 10) / 10
    : null;

  const whrLatest = waistToHip(latest.belly, latest.butt);
  const whrPrev = previous ? waistToHip(previous.belly, previous.butt) : null;
  const whrDelta = whrLatest !== null && whrPrev !== null
    ? Math.round((whrLatest - whrPrev) * 100) / 100
    : null;

  const whtLatest = waistToHeight(latest.belly, settings?.height);
  const whtPrev = previous ? waistToHeight(previous.belly, settings?.height) : null;
  const whtDelta = whtLatest !== null && whtPrev !== null
    ? Math.round((whtLatest - whtPrev) * 100) / 100
    : null;

  // Body-fat trend series (chronological), skipping entries we can't compute
  const bfTrend = [...measurements]
    .reverse()
    .map((m) => ({ date: m.date ? format(parseISO(m.date), 'MMM d') : '', bf: bodyFatFor(m, settings) }))
    .filter((d) => d.bf !== null);

  // Health hint for waist-to-height (0.5 is the common "keep below" threshold)
  const whtHealthy = whtLatest !== null && whtLatest < 0.5;

  return (
    <Card title="Body Composition" subtitle="Estimated from your measurements">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        {/* Body Fat % */}
        <div className="bg-gray-700/50 rounded-xl p-4">
          <div className="text-sm text-gray-400">Body Fat (Navy)</div>
          {missingProfile ? (
            <div className="mt-2 flex items-start gap-1.5 text-xs text-amber-400">
              <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              Set height &amp; gender in Settings to estimate body fat.
            </div>
          ) : bfLatest === null ? (
            <div className="mt-2 flex items-start gap-1.5 text-xs text-amber-400">
              <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              Needs neck &amp; waist{String(settings.gender).toLowerCase() === 'female' ? ' &amp; hip' : ''}.
            </div>
          ) : (
            <>
              <div className="text-2xl font-bold text-gray-100 mt-1">{bfLatest}%</div>
              <div className="mt-1">
                <DeltaBadge delta={bfDelta} lowerIsBetter unit="%" />
              </div>
            </>
          )}
        </div>

        {/* Waist-to-Hip */}
        <div className="bg-gray-700/50 rounded-xl p-4">
          <div className="text-sm text-gray-400">Waist-to-Hip</div>
          {whrLatest === null ? (
            <div className="mt-2 text-xs text-gray-500">Needs waist &amp; hip</div>
          ) : (
            <>
              <div className="text-2xl font-bold text-gray-100 mt-1">{whrLatest}</div>
              <div className="mt-1">
                <DeltaBadge delta={whrDelta} lowerIsBetter />
              </div>
            </>
          )}
        </div>

        {/* Waist-to-Height */}
        <div className="bg-gray-700/50 rounded-xl p-4">
          <div className="text-sm text-gray-400">Waist-to-Height</div>
          {whtLatest === null ? (
            <div className="mt-2 text-xs text-gray-500">Needs waist &amp; height</div>
          ) : (
            <>
              <div className="text-2xl font-bold text-gray-100 mt-1">{whtLatest}</div>
              <div className="mt-1 flex items-center gap-2">
                <DeltaBadge delta={whtDelta} lowerIsBetter />
                <span className={`text-xs ${whtHealthy ? 'text-green-400' : 'text-amber-400'}`}>
                  {whtHealthy ? 'healthy (<0.5)' : 'above 0.5'}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Body-fat trend */}
      {bfTrend.length > 1 && (
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Body Fat Trend</h4>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={bfTrend}>
                <defs>
                  <linearGradient id="bfGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={11} />
                <YAxis
                  stroke="#9ca3af"
                  fontSize={11}
                  domain={['dataMin - 1', 'dataMax + 1']}
                  tickFormatter={(v) => `${v}%`}
                  width={40}
                />
                <Tooltip
                  formatter={(value) => [`${value}%`, 'Body Fat']}
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#f3f4f6' }}
                />
                <Area
                  type="monotone"
                  dataKey="bf"
                  stroke="#f97316"
                  strokeWidth={2}
                  fill="url(#bfGradient)"
                  connectNulls
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </Card>
  );
}
