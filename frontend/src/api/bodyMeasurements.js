import { Capacitor } from '@capacitor/core';
const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import bodyMeasurementsOffline from './bodyMeasurements.offline';
import bodyMeasurementsOnline from './bodyMeasurements.online';

export const bodyMeasurementsApi = isOffline ? bodyMeasurementsOffline : bodyMeasurementsOnline;
export default bodyMeasurementsApi;
