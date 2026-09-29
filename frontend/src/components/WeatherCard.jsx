import { translations } from '../hooks/useTranslation';

export default function WeatherCard({ weatherData }) {
  if (!weatherData || !weatherData.features) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Weather Data</h3>
        <div className="text-gray-500 text-sm">Weather data not available</div>
      </div>
    );
  }

  const features = weatherData.features;

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">Weather Conditions</h3>
      <p className="text-xs text-gray-500 mb-4">Source: {weatherData.source}</p>

      <div className="grid grid-cols-2 gap-3">
        {features.rainfall_total !== undefined && (
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Total Rainfall</div>
            <div className="text-xl font-bold text-blue-700">{features.rainfall_total?.toFixed(0)} mm</div>
          </div>
        )}
        {features.temp_avg !== undefined && (
          <div className="bg-orange-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Avg Temperature</div>
            <div className="text-xl font-bold text-orange-700">{features.temp_avg?.toFixed(1)}°C</div>
          </div>
        )}
        {features.temp_max !== undefined && (
          <div className="bg-red-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Max Temperature</div>
            <div className="text-xl font-bold text-red-700">{features.temp_max?.toFixed(1)}°C</div>
          </div>
        )}
        {features.temp_min !== undefined && (
          <div className="bg-cyan-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Min Temperature</div>
            <div className="text-xl font-bold text-cyan-700">{features.temp_min?.toFixed(1)}°C</div>
          </div>
        )}
        {features.gdd !== undefined && (
          <div className="bg-green-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Growing Degree Days</div>
            <div className="text-xl font-bold text-green-700">{features.gdd?.toFixed(0)}</div>
          </div>
        )}
        {features.heat_stress_days !== undefined && (
          <div className="bg-yellow-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Heat Stress Days</div>
            <div className="text-xl font-bold text-yellow-700">{features.heat_stress_days?.toFixed(0)}</div>
          </div>
        )}
      </div>
    </div>
  );
}
