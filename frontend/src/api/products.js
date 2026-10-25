const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import productsOffline from './products.offline';
import productsOnline from './products.online';

export const productsAvailable = !isOffline;
export const productsApi = isOffline ? productsOffline : productsOnline;
export default productsApi;
