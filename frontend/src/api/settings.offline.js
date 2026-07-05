// Offline settings API: same exports/signatures, backed by local SQLite.
import { Capacitor } from '@capacitor/core';
import { buildSettings, updateSettings, updateFitnessGoal } from '../logic/settings';
import { buildExport } from '../logic/exportData';

async function saveAndShare({ filename, mime, content }) {
  if (Capacitor.getPlatform() === 'web') {
    // Browser: trigger a blob download.
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    return;
  }
  // Native: write to the cache dir, then open the Share sheet.
  const { Filesystem, Directory, Encoding } = await import('@capacitor/filesystem');
  const { Share } = await import('@capacitor/share');
  await Filesystem.writeFile({ path: filename, data: content, directory: Directory.Cache, encoding: Encoding.UTF8 });
  const { uri } = await Filesystem.getUri({ path: filename, directory: Directory.Cache });
  await Share.share({ title: filename, url: uri });
}

const settingsApi = {
  getSettings: () => buildSettings(),
  updateSettings: (data) => updateSettings(data),
  updateFitnessGoal: (goal) => updateFitnessGoal(goal),

  // Offline export: build the file client-side and download (web) or share (native).
  exportData: async (type = 'all', format = 'csv') => {
    const file = await buildExport(type, format);
    await saveAndShare(file);
  },
};

export default settingsApi;
