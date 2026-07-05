// Raw DB access for meal_template + meal_template_item.
import { dbAll, dbGet, dbRun } from '../sqlite';

export const mealTemplateRepo = {
  async all() { return dbAll(`SELECT * FROM meal_template ORDER BY created_at DESC;`); },
  async getById(id) { return dbGet(`SELECT * FROM meal_template WHERE id = ?;`, [id]); },
  async items(templateId) { return dbAll(`SELECT * FROM meal_template_item WHERE template_id = ?;`, [templateId]); },

  async insert({ name, created_at }) {
    const { lastId } = await dbRun(`INSERT INTO meal_template (name, created_at) VALUES (?, ?);`, [name, created_at]);
    return lastId;
  },
  async insertItem({ template_id, product_name, calories = 0, protein = 0, fat = 0, carbohydrates = 0 }) {
    await dbRun(
      `INSERT INTO meal_template_item (template_id, product_name, calories, protein, fat, carbohydrates) VALUES (?, ?, ?, ?, ?, ?);`,
      [template_id, product_name, calories, protein, fat, carbohydrates],
    );
  },
  async remove(id) { await dbRun(`DELETE FROM meal_template WHERE id = ?;`, [id]); },
};

export default mealTemplateRepo;
