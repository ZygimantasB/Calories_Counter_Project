const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import foodOffline from './food.offline';
import foodOnline from './food.online';

export const foodApi = isOffline ? foodOffline : foodOnline;
export default foodApi;
