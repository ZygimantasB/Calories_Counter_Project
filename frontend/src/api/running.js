import { Capacitor } from '@capacitor/core';
const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import runningOffline from './running.offline';
import runningOnline from './running.online';

export const runningApi = isOffline ? runningOffline : runningOnline;
export default runningApi;
