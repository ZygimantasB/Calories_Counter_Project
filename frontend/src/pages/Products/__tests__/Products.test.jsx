import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../../api/products', () => ({
  productsApi: {
    list: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn(), log: vi.fn(),
  },
}));
vi.mock('../../../api', () => ({ foodApi: { searchAllFoods: vi.fn() } }));

import { productsApi } from '../../../api/products';
import Products from '../index';

const product = {
  id: 1, name: 'Chicken tortilla', servings_yield: 2, ingredient_count: 2,
  ingredients: [],
  totals: { calories: 365, protein: 37, fat: 8.5, carbohydrates: 33 },
  per_serving: { calories: 182.5, protein: 18.5, fat: 4.25, carbohydrates: 16.5 },
};

describe('Products page', () => {
  beforeEach(() => {
    Object.values(productsApi).forEach((fn) => fn.mockReset());
    productsApi.list.mockResolvedValue({ products: [product] });
    productsApi.log.mockResolvedValue({ success: true });
    productsApi.delete.mockResolvedValue({ success: true });
  });

  it('renders products from the API', async () => {
    render(<Products />);
    expect(await screen.findByText('Chicken tortilla')).toBeInTheDocument();
    expect(screen.getByText(/183 kcal/)).toBeInTheDocument();
  });

  it('logs the chosen servings', async () => {
    const user = userEvent.setup();
    render(<Products />);
    const servings = await screen.findByLabelText('Servings of Chicken tortilla');
    await user.clear(servings);
    await user.type(servings, '1.5');
    await user.click(screen.getByRole('button', { name: 'Log' }));
    expect(productsApi.log).toHaveBeenCalledWith(1, 1.5, expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/));
  });

  it('deletes after inline confirm', async () => {
    const user = userEvent.setup();
    render(<Products />);
    await user.click(await screen.findByRole('button', { name: 'Delete' }));
    await user.click(screen.getByRole('button', { name: 'Confirm delete' }));
    expect(productsApi.delete).toHaveBeenCalledWith(1);
  });
});
