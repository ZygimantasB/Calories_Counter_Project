// Raw DB access for body_measurement.
import { dbAll, dbGet, dbRun } from '../sqlite';

export const METRIC_FIELDS = [
  'neck', 'chest', 'belly', 'left_biceps', 'right_biceps', 'left_triceps', 'right_triceps',
  'left_forearm', 'right_forearm', 'left_thigh', 'right_thigh', 'left_lower_leg', 'right_lower_leg', 'butt',
];

export const bodyRepo = {
  async all(limit = null) {
    const sql = `SELECT * FROM body_measurement ORDER BY date DESC${limit ? ` LIMIT ${Number(limit)}` : ''};`;
    return dbAll(sql);
  },
  async allAsc() { return dbAll(`SELECT * FROM body_measurement ORDER BY date ASC;`); },
  async getById(id) { return dbGet(`SELECT * FROM body_measurement WHERE id = ?;`, [id]); },

  async insert(fields) {
    const cols = ['date', ...METRIC_FIELDS, 'notes'];
    const vals = cols.map((c) => (fields[c] === undefined ? null : fields[c]));
    const { lastId } = await dbRun(
      `INSERT INTO body_measurement (${cols.join(',')}) VALUES (${cols.map(() => '?').join(',')});`, vals,
    );
    return lastId;
  },

  async update(id, fields) {
    const cols = []; const vals = [];
    for (const key of ['date', ...METRIC_FIELDS, 'notes']) {
      if (key in fields) { cols.push(`${key} = ?`); vals.push(fields[key]); }
    }
    if (!cols.length) return;
    vals.push(id);
    await dbRun(`UPDATE body_measurement SET ${cols.join(', ')} WHERE id = ?;`, vals);
  },

  async remove(id) { await dbRun(`DELETE FROM body_measurement WHERE id = ?;`, [id]); },
};

export default bodyRepo;
