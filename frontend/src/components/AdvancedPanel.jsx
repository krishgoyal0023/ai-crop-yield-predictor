export default function AdvancedPanel({ showAdvanced, onClose, onApply }) {
  if (!showAdvanced) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full p-6 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Advanced Options</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
        </div>

        <div className="space-y-6">
          {/* Weather Override */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-800 mb-3">Override Weather Data</h3>
            <p className="text-sm text-gray-600 mb-3">
              Simulate different weather conditions for what-if analysis.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Rainfall Change (%)</label>
                <input id="adv-rainfall" type="number" className="w-full px-3 py-2 border rounded-lg" placeholder="0" />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Temperature Change (°C)</label>
                <input id="adv-temp" type="number" step="0.5" className="w-full px-3 py-2 border rounded-lg" placeholder="0" />
              </div>
            </div>
          </div>

          {/* Soil Test Values */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-800 mb-3">Soil Test Values (Lab Results)</h3>
            <p className="text-sm text-gray-600 mb-3">
              Enter actual soil test results for more accurate predictions.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">pH</label>
                <input id="adv-ph" type="number" step="0.1" className="w-full px-3 py-2 border rounded-lg" placeholder="Auto" />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Nitrogen (kg/ha)</label>
                <input id="adv-n" type="number" className="w-full px-3 py-2 border rounded-lg" placeholder="Auto" />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Phosphorus (kg/ha)</label>
                <input id="adv-p" type="number" className="w-full px-3 py-2 border rounded-lg" placeholder="Auto" />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Potassium (kg/ha)</label>
                <input id="adv-k" type="number" className="w-full px-3 py-2 border rounded-lg" placeholder="Auto" />
              </div>
            </div>
          </div>

          {/* What-If Simulation */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-800 mb-3">What-If Simulation</h3>
            <p className="text-sm text-gray-600 mb-3">
              Compare predictions under different management scenarios.
            </p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <input type="checkbox" id="sim-irrigation" className="rounded" />
                <label htmlFor="sim-irrigation" className="text-sm text-gray-700">
                  Improved irrigation
                </label>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="sim-fertilizer" className="rounded" />
                <label htmlFor="sim-fertilizer" className="text-sm text-gray-700">
                  Enhanced fertilizer
                </label>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="sim-variety" className="rounded" />
                <label htmlFor="sim-variety" className="text-sm text-gray-700">
                  High-yield variety
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex gap-3">
          <button
            onClick={() => onApply && onApply()}
            className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
          >
            Apply Changes &amp; Predict
          </button>
          <button onClick={onClose} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-lg hover:bg-gray-300">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
