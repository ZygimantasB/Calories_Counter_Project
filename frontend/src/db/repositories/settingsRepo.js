// Raw DB access for the user_settings singleton (pk=1) and latest-weight lookup.
import { dbGet, dbRun } from '../sqlite';

const NUMERIC = new Set(['age', 'height', 'current_weight', 'daily_calorie_target', 'target_weight',
  'weekly_workout_goal', 'protein_target', 'carbs_target', 'fat_target', 'default_date_range']);
const BOOL = new Set(['use_auto_macros', 'meal_reminder_enabled', 'workout_reminder_enabled', 'weight_reminder_enabled']);

export const settingsRepo = {
  async get() {
    let row = await dbGet(`SELECT * FROM user_settings WHERE id = 1;`);
    if (!row) {
      await dbRun(`INSERT INTO user_settings (id) VALUES (1);`);
      row = await dbGet(`SELECT * FROM user_settings WHERE id = 1;`);
    }
    return row;
  },

  /** Most recent Weight.weight (kg) or null. */
  async latestWeight() {
    const row = await dbGet(`SELECT weight FROM weight ORDER BY recorded_at DESC LIMIT 1;`);
    return row ? Number(row.weight) : null;
  },

  /** Partial update of the settings row; unknown keys are ignored. */
  async update(data) {
    const cols = [];
    const vals = [];
    for (const [k, v] of Object.entries(data)) {
      if (k === 'id') continue;
      let value = v;
      if (BOOL.has(k)) value = v ? 1 : 0;
      else if (NUMERIC.has(k)) value = v === '' || v == null ? null : Number(v);
      else if (Array.isArray(v)) value = JSON.stringify(v);
      cols.push(`${k} = ?`);
      vals.push(value);
    }
    cols.push(`updated_at = ?`);
    vals.push(new Date().toISOString());
    await dbRun(`UPDATE user_settings SET ${cols.join(', ')} WHERE id = 1;`, vals);
    return this.get();
  },

  /** Keep current_weight synced to the latest Weight entry (mirrors api_dashboard). */
  async syncCurrentWeight() {
    const latest = await this.latestWeight();
    if (latest != null) {
      await dbRun(`UPDATE user_settings SET current_weight = ? WHERE id = 1;`, [latest]);
    }
    return latest;
  },
};

export default settingsRepo;
