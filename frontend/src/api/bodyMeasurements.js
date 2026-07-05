// Offline body-measurements API: same exports/signatures, backed by local SQLite.
import * as body from '../logic/body';
import { bodyRepo, METRIC_FIELDS } from '../db/repositories/bodyRepo';

function normalizeDate(value) {
  if (!value) return new Date().toISOString();
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split('-').map(Number);
    return new Date(y, m - 1, d, 12, 0, 0).toISOString();
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? new Date().toISOString() : parsed.toISOString();
}
const num = (v) => (v === '' || v == null ? null : Number(v));

export const bodyMeasurementsApi = {
  getMeasurements: (/* params */) => body.listMeasurements(),
  getData: (/* days */) => body.measurementsData(),

  // api_add_body_measurement maps left_calf/right_calf -> left_lower_leg/right_lower_leg
  addMeasurement: async (data) => {
    const fields = { date: normalizeDate(data.recorded_at || data.date), notes: data.notes ?? '' };
    for (const f of METRIC_FIELDS) {
      if (f === 'left_lower_leg') fields[f] = num(data.left_calf);
      else if (f === 'right_lower_leg') fields[f] = num(data.right_calf);
      else fields[f] = num(data[f]);
    }
    const id = await bodyRepo.insert(fields);
    return { success: true, id };
  },

  editMeasurement: async (measurementId, data) => {
    const fields = {};
    for (const f of [...METRIC_FIELDS, 'notes']) if (f in data) fields[f] = f === 'notes' ? data[f] : num(data[f]);
    if ('recorded_at' in data) fields.date = normalizeDate(data.recorded_at);
    await bodyRepo.update(measurementId, fields);
    return { success: true };
  },

  deleteMeasurement: async (measurementId) => { await bodyRepo.remove(measurementId); return { success: true }; },

  exportCsv: async () => {
    const content = await body.exportCsvContent();
    return new Blob([content], { type: 'text/csv' });
  },
};

export default bodyMeasurementsApi;
