import { Capacitor } from '@capacitor/core';
const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import workoutOffline from './workout.offline';
import workoutOnline from './workout.online';

export const workoutApi = isOffline ? workoutOffline : workoutOnline;
export default workoutApi;
