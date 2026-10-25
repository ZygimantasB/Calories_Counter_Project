const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import weightOffline from './weight.offline';
import weightOnline from './weight.online';

export const weightApi = isOffline ? weightOffline : weightOnline;
export default weightApi;
