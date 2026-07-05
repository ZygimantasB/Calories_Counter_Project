// Raw DB access for food_item.
import { dbAll, dbGet, dbRun } from '../sqlite';

export const foodRepo = {
  /** All rows within [startIso, endIso] (inclusive), newest first. Both optional. */
  async listBetween(startIso, endIso) {
    let sql = `SELECT * FROM food_item`;
    const params = [];
    const where = [];
    if (startIso) { where.push(`consumed_at >= ?`); params.push(startIso); }
    if (endIso) { where.push(`consumed_at <= ?`); params.push(endIso); }
    if (where.length) sql += ` WHERE ${where.join(' AND ')}`;
    sql += ` ORDER BY consumed_at DESC;`;
    return dbAll(sql, params);
  },

  async all() {
    return dbAll(`SELECT * FROM food_item ORDER BY consumed_at DESC;`);
  },

  async getById(id) {
    return dbGet(`SELECT * FROM food_item WHERE id = ?;`, [id]);
  },

  async insert({ product_name, calories = 0, protein = 0, carbohydrates = 0, fat = 0, consumed_at }) {
    const { lastId } = await dbRun(
      `INSERT INTO food_item (product_name, calories, protein, carbohydrates, fat, consumed_at, hide_from_quick_list)
       VALUES (?, ?, ?, ?, ?, ?, 0);`,
      [product_name, calories, protein, carbohydrates, fat, consumed_at],
    );
    return lastId;
  },

  async update(id, fields) {
    const map = {
      name: 'product_name', product_name: 'product_name',
      calories: 'calories', protein: 'protein',
      carbs: 'carbohydrates', carbohydrates: 'carbohydrates', fat: 'fat',
      consumed_at: 'consumed_at', hidden: 'hide_from_quick_list', hide_from_quick_list: 'hide_from_quick_list',
    };
    const cols = [];
    const vals = [];
    for (const [k, v] of Object.entries(fields)) {
      const col = map[k];
      if (!col) continue;
      cols.push(`${col} = ?`);
      vals.push(col === 'hide_from_quick_list' ? (v ? 1 : 0) : v);
    }
    if (!cols.length) return;
    vals.push(id);
    await dbRun(`UPDATE food_item SET ${cols.join(', ')} WHERE id = ?;`, vals);
  },

  async remove(id) {
    await dbRun(`DELETE FROM food_item WHERE id = ?;`, [id]);
  },

  async setHidden(id, hidden) {
    await dbRun(`UPDATE food_item SET hide_from_quick_list = ? WHERE id = ?;`, [hidden ? 1 : 0, id]);
  },
};

export default foodRepo;
