// Port of api_meal_templates, api_add_meal_template, api_apply_meal_template, api_delete_meal_template.
import { mealTemplateRepo } from '../db/repositories/mealTemplateRepo';
import { foodRepo } from '../db/repositories/foodRepo';

function localDayBoundsIso(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  return {
    startIso: new Date(y, m - 1, d, 0, 0, 0, 0).toISOString(),
    endIso: new Date(y, m - 1, d, 23, 59, 59, 999).toISOString(),
  };
}
function todayLocal() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// ---- api_meal_templates ----
export async function list() {
  const templates = await mealTemplateRepo.all();
  const result = [];
  for (const t of templates) {
    const items = await mealTemplateRepo.items(t.id);
    result.push({
      id: t.id,
      name: t.name,
      created_at: t.created_at,
      items_count: items.length,
      total_calories: items.reduce((s, i) => s + (Number(i.calories) || 0), 0),
    });
  }
  return { templates: result };
}

// ---- api_add_meal_template (save a day's foods as a template) ----
export async function save(name, date = null) {
  const trimmed = String(name ?? '').trim();
  if (!trimmed) return { success: false, message: 'Template name is required' };

  const { startIso, endIso } = localDayBoundsIso(date || todayLocal());
  const foods = await foodRepo.listBetween(startIso, endIso);
  if (!foods.length) return { success: false, message: 'No food items found for this day' };

  const templateId = await mealTemplateRepo.insert({ name: trimmed, created_at: new Date().toISOString() });
  for (const item of foods) {
    await mealTemplateRepo.insertItem({
      template_id: templateId,
      product_name: item.product_name,
      calories: Number(item.calories) || 0,
      fat: Number(item.fat) || 0,
      carbohydrates: Number(item.carbohydrates) || 0,
      protein: Number(item.protein) || 0,
    });
  }
  return { success: true, id: templateId, items_count: foods.length };
}

// ---- api_apply_meal_template (log the template's items as food for today) ----
export async function apply(templateId) {
  const template = await mealTemplateRepo.getById(templateId);
  if (!template) return { success: false, message: 'Template not found' };
  const items = await mealTemplateRepo.items(templateId);
  const now = new Date().toISOString();
  for (const item of items) {
    await foodRepo.insert({
      product_name: item.product_name,
      calories: Number(item.calories) || 0,
      fat: Number(item.fat) || 0,
      carbohydrates: Number(item.carbohydrates) || 0,
      protein: Number(item.protein) || 0,
      consumed_at: now,
    });
  }
  return { success: true, items_logged: items.length };
}

// ---- api_delete_meal_template ----
export async function remove(templateId) {
  await mealTemplateRepo.remove(templateId);
  return { success: true };
}
