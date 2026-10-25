import { describe, it, expect } from 'vitest';

describe('products API selector', () => {
  it('uses the offline stub in test mode and reports products unavailable', async () => {
    const { productsApi, productsAvailable } = await import('../products');
    const { default: productsOffline } = await import('../products.offline');
    expect(productsApi).toBe(productsOffline);
    expect(productsAvailable).toBe(false);
  });

  it('offline stub rejects every call', async () => {
    const { default: productsOffline } = await import('../products.offline');
    await expect(productsOffline.list()).rejects.toThrow('Products are not available offline');
    await expect(productsOffline.log(1)).rejects.toThrow('Products are not available offline');
  });
});
