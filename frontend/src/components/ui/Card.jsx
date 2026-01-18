export default function Card({
  children,
  title,
  subtitle,
  action,
  className = '',
  padding = true,
  hover = false,
}) {
  return (
    <div
      className={`bg-gray-800 rounded-xl shadow-lg border border-gray-700 ${
        hover ? 'hover:shadow-xl hover:border-gray-600 transition-all duration-200' : ''
      } ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-400 mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={padding ? 'p-6' : ''}>{children}</div>
    </div>
  );
}
