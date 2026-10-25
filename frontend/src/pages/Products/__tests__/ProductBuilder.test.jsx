import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../../api', () => ({
  foodApi: { searchAllFoods: vi.fn() },
}));

import { foodApi } from '../../../api';
import ProductBuilder from '../ProductBuilder';

describe('ProductBuilder', () => {
  beforeEach(() => {
    foodApi.searchAllFoods.mockReset();
    foodApi.searchAllFoods.mockResolvedValue({
      results: [{ name: 'Wrap', calories: 200, protein: 6, carbs: 33, fat: 5 }],
    });
  });

  it('adds an ingredient from search and updates totals', async () => {
    const user = userEvent.setup();
    render(<ProductBuilder initial={null} onSave={vi.fn()} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText('Search your foods'), 'wr');
    await user.click(await screen.findByRole('button', { name: /Wrap — 200 kcal/ }));

    expect(screen.getByDisplayValue('Wrap')).toBeInTheDocument();
    expect(screen.getByTestId('per-serving')).toHaveTextContent('200 kcal');
  });

  it('adds and removes manual rows', async () => {
    const user = userEvent.setup();
    render(<ProductBuilder initial={null} onSave={vi.fn()} onCancel={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Add manual ingredient' }));
    await user.click(screen.getByRole('button', { name: 'Add manual ingredient' }));
    expect(screen.getAllByLabelText('Ingredient name')).toHaveLength(2);

    await user.click(screen.getAllByRole('button', { name: 'Remove ingredient' })[0]);
    expect(screen.getAllByLabelText('Ingredient name')).toHaveLength(1);
  });

  it('blocks submit without a name or ingredients', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(<ProductBuilder initial={null} onSave={onSave} onCancel={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Save product' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Name is required');
    expect(onSave).not.toHaveBeenCalled();
  });

  it('submits a numeric payload, dividing totals by yield', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<ProductBuilder initial={null} onSave={onSave} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText('Product name'), 'Tortilla');
    const yieldInput = screen.getByLabelText('Makes N servings');
    await user.clear(yieldInput);
    await user.type(yieldInput, '2');
    await user.click(screen.getByRole('button', { name: 'Add manual ingredient' }));
    const row = screen.getAllByTestId('ingredient-row')[0];
    await user.type(within(row).getByLabelText('Ingredient name'), 'Cheese');
    const kcal = within(row).getByLabelText('Calories');
    await user.clear(kcal);
    await user.type(kcal, '100');

    expect(screen.getByTestId('per-serving')).toHaveTextContent('50 kcal');
    await user.click(screen.getByRole('button', { name: 'Save product' }));

    expect(onSave).toHaveBeenCalledWith({
      name: 'Tortilla',
      servings_yield: 2,
      ingredients: [{ name: 'Cheese', calories: 100, protein: 0, fat: 0, carbohydrates: 0, quantity: 1 }],
    });
  });

  it('prefills when editing', () => {
    const initial = {
      id: 3, name: 'Burrito', servings_yield: 1,
      ingredients: [{ id: 9, name: 'Beans', calories: 120, protein: 7, fat: 1, carbohydrates: 20, quantity: 2 }],
    };
    render(<ProductBuilder initial={initial} onSave={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByDisplayValue('Burrito')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Beans')).toBeInTheDocument();
    expect(screen.getByTestId('per-serving')).toHaveTextContent('240 kcal');
  });
});
