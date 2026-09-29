import { useState } from 'react';
import ReliabilityBadge from './ReliabilityBadge';
import SoilCard from './SoilCard';
import WeatherCard from './WeatherCard';
import CropInfo from './CropInfo';

export default function PredictionResult({ result, onReset }) {
  const [showCropInfo, setShowCropInfo] = useState(false);

  if (!result) return null;

  const getReliabilityColor = (reliability) => {
    const colors = {
      High: 'text-green-600 bg-green-50 border-green-200',
      Medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      Low: 'text-red-600 bg-red-50 border-red-200',
    };
    return colors[reliability] || colors.Medium;
  };

  const deviationPositive = result.deviation_from_baseline > 0;
  const deviationPercent = result.historical_baseline > 0
    ? ((result.deviation_from_baseline / result.historical_baseline) * 100).toFixed(1)
    : 0;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Main Result Card */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl shadow-lg p-6 border-2 border-green-200">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-800 mb-1">
              Predicted Yield
            </h2>
            <p className="text-sm text-gray-600">
              {result.crop} • {result.district}
            </p>
          </div>
          <button
            onClick={() => setShowCropInfo(true)}
            className="text-sm bg-green-600 text-white px-3 py-1 rounded-lg hover:bg-green-700"
          >
            Crop Info
          </button>
        </div>

        <div className="text-5xl font-bold text-green-700 mb-2">
          {result.predicted_yield}
          <span className="text-2xl text-gray-600 ml-2">t/ha</span>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
          <span>
            vs District: <strong>{result.historical_baseline} t/ha</strong>
          </span>
          <span className={deviationPositive ? 'text-green-600' : 'text-red-600'}>
            {deviationPositive ? '↑' : '↓'} {Math.abs(deviationPercent)}%
          </span>
        </div>

        <div className="bg-white rounded-lg p-4 mb-4">
          <div className="text-sm text-gray-600 mb-2">Confidence Interval (95%)</div>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold text-gray-800">
              {result.prediction_interval.lower} - {result.prediction_interval.upper}
            </span>
            <span className="text-sm text-gray-500">t/ha</span>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Method: {result.prediction_interval.method}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-600 mb-1">Reliability</div>
            <ReliabilityBadge reliability={result.reliability} />
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600 mb-1">Data Completeness</div>
            <div className="text-2xl font-bold text-gray-800">
              {(result.data_completeness * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Reliability Reasons */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Reliability Assessment</h3>
        <ul className="space-y-2">
          {result.reliability_reasons.map((reason, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
              <span className="text-green-500 mt-0.5">•</span>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* Data Sources */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Data Sources</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {Object.entries(result.data_sources).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span className="text-gray-600 capitalize">{key}:</span>
              <span className="text-gray-800 font-medium">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Key Features */}
      {result.important_features && result.important_features.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Key Factors</h3>
          <div className="space-y-2">
            {result.important_features.map((feature, idx) => (
              <div key={idx} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                <span className="text-sm text-gray-700 capitalize">
                  {feature.feature.replace(/_/g, ' ')}
                </span>
                <span className="text-sm font-semibold text-gray-800">
                  {feature.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanation */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Explanation</h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          {result.explanation}
        </p>
      </div>

      {/* Disclaimer */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
        <p className="text-xs text-yellow-800">
          <strong>Disclaimer:</strong> {result.disclaimer}
        </p>
      </div>

      {/* New Prediction Button */}
      <button
        onClick={onReset}
        className="w-full bg-gray-600 text-white py-3 rounded-lg font-medium hover:bg-gray-700 transition-colors"
      >
        New Prediction
      </button>

      {/* Crop Info Modal */}
      {showCropInfo && (
        <CropInfo crop={result.crop} onClose={() => setShowCropInfo(false)} />
      )}
    </div>
  );
}
