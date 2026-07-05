// Raw DB access for weight.
import { dbAll, dbGet, dbRun } from '../sqlite';

export const weightRepo = {
  /** Rows within [startIso, endIso] (inclusive), newest first. Both optional. */
  async listBetween(startIso, endIso) {
    let sql = `SELECT * FROM weight`;
    const params = [];
    const where = [];
    if (startIso) { where.push(`recorded_at >= ?`); params.push(startIso); }
    if (endIso) { where.push(`recorded_at <= ?`); params.push(endIso); }
    if (where.length) sql += ` WHERE ${where.join(' AND ')}`;
    sql += ` ORDER BY recorded_at DESC;`;
    return dbAll(sql, params);
  },

  async all() {
    return dbAll(`SELECT * FROM weight ORDER BY recorded_at DESC;`);
  },

  /** Chronological (oldest first) — used for correlation/pace math. */
  async allAsc() {
    return dbAll(`SELECT * FROM weight ORDER BY recorded_at ASC;`);
  },

  async getById(id) {
    return dbGet(`SELECT * FROM weight WHERE id = ?;`, [id]);
  },

  async insert({ weight, recorded_at, notes = null }) {
    const { lastId } = await dbRun(
      `INSERT INTO weight (weight, recorded_at, notes) VALUES (?, ?, ?);`,
      [weight, recorded_at, notes],
    );
    return lastId;
  },

  async update(id, fields) {
    const cols = [];
    const vals = [];
    for (const key of ['weight', 'recorded_at', 'notes']) {
      if (key in fields) { cols.push(`${key} = ?`); vals.push(fields[key]); }
    }
    if (!cols.length) return;
    vals.push(id);
    await dbRun(`UPDATE weight SET ${cols.join(', ')} WHERE id = ?;`, vals);
  },

  async remove(id) {
    await dbRun(`DELETE FROM weight WHERE id = ?;`, [id]);
  },
};

export default weightRepo;
