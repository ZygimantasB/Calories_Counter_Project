import { useState } from 'react';
import Card from './ui/Card';

const BUTTONS = [
  ['C', '(', ')', '/'],
  ['7', '8', '9', '×'],
  ['4', '5', '6', '-'],
  ['1', '2', '3', '+'],
  ['0', '.', '='],
];

function safeEval(expression) {
  // Only allow digits, operators, parens, decimal points, and whitespace
  if (!/^[\d\s()+\-*/.]+$/.test(expression)) {
    return 'Error';
  }
  try {
    // eslint-disable-next-line no-new-func
    const result = Function('"use strict"; return (' + expression + ')')();
    if (!isFinite(result) || isNaN(result)) return 'Error';
    // Return clean number string (avoid floating point noise)
    const str = String(parseFloat(result.toFixed(10)));
    return str;
  } catch {
    return 'Error';
  }
}

export default function Calculator({ onCopyValue }) {
  const [display, setDisplay] = useState('0');

  const handleButton = (label) => {
    if (label === 'C') {
      setDisplay('0');
      return;
    }

    if (label === '=') {
      // Replace display × with * for evaluation
      const expr = display.replace(/×/g, '*');
      const result = safeEval(expr);
      setDisplay(result);
      return;
    }

    setDisplay((prev) => {
      // If current display is '0' or 'Error', replace it (unless appending operator/paren)
      if (prev === '0' || prev === 'Error') {
        if (['+', '-', '/', '×', ')'].includes(label)) {
          return prev === 'Error' ? label : prev + label;
        }
        return label;
      }
      return prev + label;
    });
  };

  const handleDisplayChange = (e) => {
    setDisplay(e.target.value);
  };

  const handleCopy = (field) => {
    if (onCopyValue) {
      onCopyValue(field, display);
    }
  };

  const getButtonClass = (label) => {
    if (label === 'C') {
      return 'p-3 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium text-lg transition-colors';
    }
    if (label === '=') {
      return 'p-3 rounded-lg bg-primary-500 hover:bg-primary-600 text-white font-medium text-lg transition-colors';
    }
    if (['+', '-', '×', '/', '(', ')'].includes(label)) {
      return 'p-3 rounded-lg bg-primary-500/20 hover:bg-primary-500/30 text-primary-400 font-medium text-lg transition-colors';
    }
    return 'p-3 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-100 font-medium text-lg transition-colors';
  };

  return (
    <Card title="Calculator">
      <div className="space-y-3">
        {/* Display */}
        <input
          type="text"
          value={display}
          onChange={handleDisplayChange}
          className="w-full px-4 py-3 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 text-right text-xl font-mono"
          aria-label="Calculator display"
        />

        {/* Button Grid */}
        <div className="space-y-1.5">
          {BUTTONS.map((row, rowIndex) => (
            <div
              key={rowIndex}
              className={`grid gap-1.5 ${row.length === 4 ? 'grid-cols-4' : 'grid-cols-4'}`}
            >
              {row.map((label) => (
                <button
                  key={label}
                  onClick={() => handleButton(label)}
                  className={`${getButtonClass(label)} ${label === '0' && row.length === 3 ? 'col-span-2' : ''}`}
                  aria-label={label}
                >
                  {label}
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Copy Buttons */}
        <div className="pt-2 border-t border-gray-700 space-y-2">
          <button
            onClick={() => handleCopy('calories')}
            className="w-full py-2 rounded-lg bg-primary-500 hover:bg-primary-600 text-white font-medium text-sm transition-colors"
          >
            Copy to Calories
          </button>
          <div className="grid grid-cols-3 gap-1.5">
            <button
              onClick={() => handleCopy('fat')}
              className="py-2 rounded-lg bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 font-medium text-sm transition-colors"
            >
              Fat
            </button>
            <button
              onClick={() => handleCopy('carbs')}
              className="py-2 rounded-lg bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 font-medium text-sm transition-colors"
            >
              Carbs
            </button>
            <button
              onClick={() => handleCopy('protein')}
              className="py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium text-sm transition-colors"
            >
              Protein
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}
