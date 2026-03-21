import { Download } from 'lucide-react';

export default function CSVDownloadButton({ endpoint, params = {}, label = 'Download CSV', className = '' }) {
  const handleDownload = () => {
    const searchParams = new URLSearchParams(params);
    searchParams.set('export', 'csv');
    window.location.href = `${endpoint}?${searchParams.toString()}`;
  };

  return (
    <button
      onClick={handleDownload}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 text-sm font-medium transition-colors ${className}`}
    >
      <Download className="w-4 h-4" />
      {label}
    </button>
  );
}
