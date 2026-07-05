import { Capacitor } from '@capacitor/core';
const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import settingsOffline from './settings.offline';
import settingsOnline from './settings.online';

export const settingsApi = isOffline ? settingsOffline : settingsOnline;
export default settingsApi;
