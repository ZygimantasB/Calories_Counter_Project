import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Calculator from '../Calculator';

describe('Calculator Component', () => {
  const mockOnCopyValue = vi.fn();

  beforeEach(() => {
    mockOnCopyValue.mockClear();
  });

  describe('Rendering', () => {
    it('renders all calculator buttons', () => {
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      // Digit buttons
      ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'].forEach((digit) => {
        expect(screen.getByRole('button', { name: digit })).toBeInTheDocument();
      });

      // Operator buttons
      expect(screen.getByRole('button', { name: '+' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '-' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '×' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '/' })).toBeInTheDocument();

      // Other buttons
      expect(screen.getByRole('button', { name: 'C' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '(' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: ')' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '.' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '=' })).toBeInTheDocument();

      // Copy buttons
      expect(screen.getByRole('button', { name: /copy to calories/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /fat/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /carbs/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /protein/i })).toBeInTheDocument();
    });

    it('renders the Calculator card title', () => {
      render(<Calculator onCopyValue={mockOnCopyValue} />);
      expect(screen.getByText('Calculator')).toBeInTheDocument();
    });

    it('shows 0 as initial display value', () => {
      render(<Calculator onCopyValue={mockOnCopyValue} />);
      const display = screen.getByRole('textbox');
      expect(display.value).toBe('0');
    });
  });

  describe('Basic Calculation', () => {
    it('performs addition: 5+3=8', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '5' }));
      await user.click(screen.getByRole('button', { name: '+' }));
      await user.click(screen.getByRole('button', { name: '3' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      const display = screen.getByRole('textbox');
      expect(display.value).toBe('8');
    });

    it('performs subtraction', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '9' }));
      await user.click(screen.getByRole('button', { name: '-' }));
      await user.click(screen.getByRole('button', { name: '4' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      const display = screen.getByRole('textbox');
      expect(display.value).toBe('5');
    });

    it('performs multiplication', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '3' }));
      await user.click(screen.getByRole('button', { name: '×' }));
      await user.click(screen.getByRole('button', { name: '4' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      const display = screen.getByRole('textbox');
      expect(display.value).toBe('12');
    });

    it('performs division', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '8' }));
      await user.click(screen.getByRole('button', { name: '/' }));
      await user.click(screen.getByRole('button', { name: '2' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      const display = screen.getByRole('textbox');
      expect(display.value).toBe('4');
    });
  });

  describe('Clear Button', () => {
    it('resets display to 0 after entering values', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '5' }));
      await user.click(screen.getByRole('button', { name: '+' }));
      await user.click(screen.getByRole('button', { name: '3' }));

      await user.click(screen.getByRole('button', { name: 'C' }));

      const display = screen.getByRole('textbox');
      expect(display.value).toBe('0');
    });
  });

  describe('Copy Buttons', () => {
    it('calls onCopyValue with "calories" and the computed result', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '2' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      await user.click(screen.getByRole('button', { name: /copy to calories/i }));

      expect(mockOnCopyValue).toHaveBeenCalledWith('calories', '2');
    });

    it('calls onCopyValue with "fat" when fat button is clicked', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '5' }));
      await user.click(screen.getByRole('button', { name: '+' }));
      await user.click(screen.getByRole('button', { name: '3' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      await user.click(screen.getByRole('button', { name: /fat/i }));

      expect(mockOnCopyValue).toHaveBeenCalledWith('fat', '8');
    });

    it('calls onCopyValue with "carbs" when carbs button is clicked', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '6' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      await user.click(screen.getByRole('button', { name: /carbs/i }));

      expect(mockOnCopyValue).toHaveBeenCalledWith('carbs', '6');
    });

    it('calls onCopyValue with "protein" when protein button is clicked', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      await user.click(screen.getByRole('button', { name: '7' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      await user.click(screen.getByRole('button', { name: /protein/i }));

      expect(mockOnCopyValue).toHaveBeenCalledWith('protein', '7');
    });
  });

  describe('Parentheses', () => {
    it('handles expressions with parentheses', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      // (2+3)*4 = 20
      await user.click(screen.getByRole('button', { name: '(' }));
      await user.click(screen.getByRole('button', { name: '2' }));
      await user.click(screen.getByRole('button', { name: '+' }));
      await user.click(screen.getByRole('button', { name: '3' }));
      await user.click(screen.getByRole('button', { name: ')' }));
      await user.click(screen.getByRole('button', { name: '×' }));
      await user.click(screen.getByRole('button', { name: '4' }));
      await user.click(screen.getByRole('button', { name: '=' }));

      const display = screen.getByRole('textbox');
      expect(display.value).toBe('20');
    });
  });

  describe('Invalid Expression', () => {
    it('shows Error for invalid expressions', async () => {
      const user = userEvent.setup();
      render(<Calculator onCopyValue={mockOnCopyValue} />);

      // Enter invalid expression via the text input directly
      const display = screen.getByRole('textbox');
      await user.clear(display);
      await user.type(display, '++');
      await user.click(screen.getByRole('button', { name: '=' }));

      expect(display.value).toBe('Error');
    });
  });
});
