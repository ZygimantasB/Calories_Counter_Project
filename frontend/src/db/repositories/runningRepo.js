// Raw DB access for running_session (duration stored as duration_seconds INTEGER).
import { dbAll, dbGet, dbRun } from '../sqlite';

export const runningRepo = {
  async listFrom(startIso) {
    if (!startIso) return dbAll(`SELECT * FROM running_session ORDER BY date DESC;`);
    return dbAll(`SELECT * FROM running_session WHERE date >= ? ORDER BY date DESC;`, [startIso]);
  },
  async all() { return dbAll(`SELECT * FROM running_session ORDER BY date DESC;`); },
  async getById(id) { return dbGet(`SELECT * FROM running_session WHERE id = ?;`, [id]); },

  async insert({ date, distance, duration_seconds, notes = '' }) {
    const { lastId } = await dbRun(
      `INSERT INTO running_session (date, distance, duration_seconds, notes) VALUES (?, ?, ?, ?);`,
      [date, distance, duration_seconds, notes],
    );
    return lastId;
  },

  async update(id, fields) {
    const cols = [];
    const vals = [];
    for (const key of ['date', 'distance', 'duration_seconds', 'notes']) {
      if (key in fields) { cols.push(`${key} = ?`); vals.push(fields[key]); }
    }
    if (!cols.length) return;
    vals.push(id);
    await dbRun(`UPDATE running_session SET ${cols.join(', ')} WHERE id = ?;`, vals);
  },

  async remove(id) { await dbRun(`DELETE FROM running_session WHERE id = ?;`, [id]); },
};

export default runningRepo;
