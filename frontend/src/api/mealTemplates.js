import { Capacitor } from '@capacitor/core';
const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import mealTemplatesOffline from './mealTemplates.offline';
import mealTemplatesOnline from './mealTemplates.online';

export const mealTemplatesApi = isOffline ? mealTemplatesOffline : mealTemplatesOnline;
export default mealTemplatesApi;
