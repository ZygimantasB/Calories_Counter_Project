// Offline composite-products API: not supported yet (phase 2). Same signatures as online.
const unavailable = () => Promise.reject(new Error('Products are not available offline'));

export const productsApi = {
  list: unavailable,
  create: unavailable,
  update: unavailable,
  delete: unavailable,
  log: unavailable,
};

export default productsApi;
