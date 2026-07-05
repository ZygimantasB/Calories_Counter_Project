import { Capacitor } from '@capacitor/core';
const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import analyticsOffline from './analytics.offline';
import analyticsOnline from './analytics.online';

export const analyticsApi = isOffline ? analyticsOffline : analyticsOnline;
export default analyticsApi;
