import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '../Button';

// Mock icon component
const MockIcon = () => <span data-testid="mock-icon">Icon</span>;

describe('Button Component', () => {
  describe('Rendering', () => {
    it('should render with default props', () => {
      render(<Button>Click Me</Button>);

      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
    });

    it('should render with children text', () => {
      render(<Button>Test Button</Button>);

      expect(screen.getByText('Test Button')).toBeInTheDocument();
    });

    it('should apply custom className', () => {
      render(<Button className="custom-class">Button</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('Variants', () => {
    it('should render primary variant (default)', () => {
      render(<Button>Primary</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-primary-500');
    });

    it('should render secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-gray-100');
    });

    it('should render ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-transparent');
    });

    it('should render danger variant', () => {
      render(<Button variant="danger">Danger</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-red-500');
    });

    it('should render success variant', () => {
      render(<Button variant="success">Success</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-green-500');
    });

    it('should render outline variant', () => {
      render(<Button variant="outline">Outline</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-white');
      expect(button).toHaveClass('border');
    });
  });

  describe('Sizes', () => {
    it('should render medium size (default)', () => {
      render(<Button>Medium</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('px-4', 'py-2', 'text-sm');
    });

    it('should render small size', () => {
      render(<Button size="sm">Small</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('px-3', 'py-1.5', 'text-sm');
    });

    it('should render large size', () => {
      render(<Button size="lg">Large</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('px-5', 'py-2.5', 'text-base');
    });

    it('should render extra large size', () => {
      render(<Button size="xl">Extra Large</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('px-6', 'py-3', 'text-base');
    });
  });

  describe('Icons', () => {
    it('should render icon on the left by default', () => {
      render(<Button icon={MockIcon}>With Icon</Button>);

      const icon = screen.getByTestId('mock-icon');
      const button = screen.getByRole('button');

      expect(icon).toBeInTheDocument();
      // Icon should be before the text in the DOM
      const children = Array.from(button.childNodes);
      const iconIndex = children.findIndex((node) =>
        node.textContent?.includes('Icon')
      );
      const textIndex = children.findIndex((node) =>
        node.textContent?.includes('With Icon')
      );
      expect(iconIndex).toBeLessThan(textIndex);
    });

    it('should render icon on the right when specified', () => {
      render(
        <Button icon={MockIcon} iconPosition="right">
          With Icon
        </Button>
      );

      const icon = screen.getByTestId('mock-icon');
      expect(icon).toBeInTheDocument();
    });

    it('should not render icon when loading', () => {
      render(
        <Button icon={MockIcon} loading>
          Loading
        </Button>
      );

      expect(screen.queryByTestId('mock-icon')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when loading is true', () => {
      render(<Button loading>Loading</Button>);

      const button = screen.getByRole('button');
      const spinner = button.querySelector('.animate-spin');

      expect(spinner).toBeInTheDocument();
      expect(button).toBeDisabled();
    });

    it('should disable button when loading', () => {
      render(<Button loading>Loading</Button>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should hide icon when loading', () => {
      render(
        <Button icon={MockIcon} loading>
          Loading
        </Button>
      );

      expect(screen.queryByTestId('mock-icon')).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50');
    });

    it('should not trigger onClick when disabled', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();

      render(
        <Button onClick={handleClick} disabled>
          Disabled
        </Button>
      );

      const button = screen.getByRole('button');
      await user.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('User Interactions', () => {
    it('should call onClick handler when clicked', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();

      render(<Button onClick={handleClick}>Click Me</Button>);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should not call onClick when loading', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();

      render(
        <Button onClick={handleClick} loading>
          Loading
        </Button>
      );

      const button = screen.getByRole('button');
      await user.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('should support form submission with type="submit"', () => {
      render(<Button type="submit">Submit</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('type', 'submit');
    });
  });

  describe('Ref Forwarding', () => {
    it('should forward ref to button element', () => {
      const ref = { current: null };

      render(<Button ref={ref}>Button</Button>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria attributes when disabled', () => {
      render(<Button disabled>Disabled</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('disabled');
    });

    it('should maintain focus styles', () => {
      render(<Button>Focus Me</Button>);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2');
    });

    it('should support aria-label', () => {
      render(<Button aria-label="Custom Label">Button</Button>);

      const button = screen.getByLabelText('Custom Label');
      expect(button).toBeInTheDocument();
    });
  });

  describe('Combined Props', () => {
    it('should render with multiple props combined', () => {
      const handleClick = vi.fn();

      render(
        <Button
          variant="danger"
          size="lg"
          icon={MockIcon}
          iconPosition="right"
          onClick={handleClick}
          className="custom-class"
        >
          Complex Button
        </Button>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-red-500');
      expect(button).toHaveClass('px-5', 'py-2.5');
      expect(button).toHaveClass('custom-class');
      expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
    });

    it('should handle all states correctly', () => {
      const { rerender } = render(<Button>Normal</Button>);

      let button = screen.getByRole('button');
      expect(button).not.toBeDisabled();

      rerender(<Button loading>Loading</Button>);
      button = screen.getByRole('button');
      expect(button).toBeDisabled();

      rerender(<Button disabled>Disabled</Button>);
      button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });
});
