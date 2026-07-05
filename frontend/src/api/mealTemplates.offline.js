// Offline meal-templates API: same exports/signatures, backed by local SQLite.
import * as mealTemplates from '../logic/mealTemplates';

export const mealTemplatesApi = {
  list: () => mealTemplates.list(),
  save: (name, date = null) => mealTemplates.save(name, date),
  apply: (templateId) => mealTemplates.apply(templateId),
  delete: (templateId) => mealTemplates.remove(templateId),
};

export default mealTemplatesApi;
