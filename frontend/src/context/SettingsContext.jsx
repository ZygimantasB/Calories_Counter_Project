// App-wide settings: loads the offline settings once, applies the theme, and
// exposes derived preferences (chart color, default range, unit + number
// formatters, week start) so every page renders consistently.
import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { settingsApi } from '../api';

const CHART_COLORS = {
  blue: '#3b82f6', green: '#10b981', purple: '#8b5cf6', orange: '#f97316', pink: '#ec4899',
};

const SettingsContext = createContext(null);

/** Resolve 'auto' to the OS preference; returns 'light' | 'dark'. */
function resolveTheme(theme) {
  if (theme === 'light' || theme === 'dark') return theme;
  const prefersDark = typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)').matches : true;
  return prefersDark ? 'dark' : 'light';
}

/** Stamp the resolved theme on <html> so the CSS palette remap kicks in. */
export function applyTheme(theme) {
  const resolved = resolveTheme(theme);
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;
}

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const data = await settingsApi.getSettings();
    setSettings(data);
    applyTheme(data?.appearance?.theme || 'dark');
    return data;
  }, []);

  useEffect(() => {
    load().catch((e) => console.error('settings load failed', e)).finally(() => setLoading(false));
  }, [load]);

  // Follow OS changes while in 'auto'.
  useEffect(() => {
    if (settings?.appearance?.theme !== 'auto' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => applyTheme('auto');
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [settings?.appearance?.theme]);

  const value = useMemo(() => {
    const appearance = settings?.appearance || {};
    const profile = settings?.profile || {};
    const weightUnit = profile.weight_unit || 'kg';
    const lengthUnit = profile.length_unit || 'cm';
    const weekStartsOn = profile.week_start === 'sunday' ? 0 : 1; // 1 = Monday (default)
    const compact = !!profile.compact_numbers;

    const fmtNum = (n, decimals = 0) => {
      const v = Number(n) || 0;
      if (compact && Math.abs(v) >= 1000) {
        return `${(v / 1000).toFixed(v % 1000 === 0 ? 0 : 1)}k`;
      }
      return v.toFixed(decimals);
    };

    return {
      settings,
      loading,
      reloadSettings: load,
      setLocalTheme: (t) => { applyTheme(t); }, // instant preview before save
      chartColor: CHART_COLORS[appearance.chart_color] || CHART_COLORS.blue,
      chartColorName: appearance.chart_color || 'blue',
      defaultRange: appearance.default_date_range || 30,
      theme: resolveTheme(appearance.theme || 'dark'),
      weekStartsOn,
      units: { weight: weightUnit, length: lengthUnit },
      // Display helpers (weight stored in kg, lengths in cm).
      formatWeight: (kg, { withUnit = true, decimals = 1 } = {}) => {
        const v = weightUnit === 'lb' ? Number(kg) * 2.2046226218 : Number(kg);
        return `${fmtNum(v, decimals)}${withUnit ? ` ${weightUnit}` : ''}`;
      },
      formatLength: (cm, { withUnit = true, decimals = 1 } = {}) => {
        const v = lengthUnit === 'in' ? Number(cm) / 2.54 : Number(cm);
        return `${fmtNum(v, decimals)}${withUnit ? ` ${lengthUnit}` : ''}`;
      },
      formatNumber: fmtNum,
    };
  }, [settings, loading, load]);

  // Hold first paint until settings are loaded: pages read defaults (range,
  // theme) at mount, and it avoids a dark→light theme flash.
  if (loading) {
    return <div style={{ minHeight: '100vh', background: 'var(--color-gray-900, #0b0f17)' }} />;
  }
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within <SettingsProvider>');
  return ctx;
}

export { CHART_COLORS };
