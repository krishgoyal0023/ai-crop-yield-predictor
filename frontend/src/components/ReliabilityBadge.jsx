import { translations } from '../hooks/useTranslation';

export default function ReliabilityBadge({ reliability }) {
  const colors = {
    High: 'bg-green-100 text-green-800 border-green-300',
    Medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    Low: 'bg-red-100 text-red-800 border-red-300',
  };

  const labels = {
    High: 'High',
    Medium: 'Medium',
    Low: 'Low',
  };

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${colors[reliability] || colors.Medium}`}>
      {labels[reliability] || 'Medium'}
    </span>
  );
}
