export default function SoilCard({ soilData }) {
  if (!soilData || !soilData.properties) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Soil Information</h3>
        <div className="text-gray-500 text-sm">Soil data not available</div>
      </div>
    );
  }

  const props = soilData.properties;
  const getSoilColor = (type) => {
    const colors = {
      'Sand': 'bg-yellow-100 text-yellow-800',
      'Loamy Sand': 'bg-amber-100 text-amber-800',
      'Loam': 'bg-green-100 text-green-800',
      'Clay Loam': 'bg-orange-100 text-orange-800',
      'Sandy Clay': 'bg-red-100 text-red-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">Soil Information</h3>
      <p className="text-xs text-gray-500 mb-4">Source: {soilData.source}</p>

      {props.Soil_Type && (
        <div className="mb-4">
          <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getSoilColor(props.Soil_Type)}`}>
            {props.Soil_Type}
          </span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {props.pH !== undefined && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">pH</div>
            <div className="text-lg font-semibold text-gray-800">{props.pH?.toFixed(1)}</div>
          </div>
        )}
        {props.N !== undefined && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Nitrogen (kg/ha)</div>
            <div className="text-lg font-semibold text-gray-800">{props.N?.toFixed(0)}</div>
          </div>
        )}
        {props.P !== undefined && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Phosphorus (kg/ha)</div>
            <div className="text-lg font-semibold text-gray-800">{props.P?.toFixed(0)}</div>
          </div>
        )}
        {props.K !== undefined && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Potassium (kg/ha)</div>
            <div className="text-lg font-semibold text-gray-800">{props.K?.toFixed(0)}</div>
          </div>
        )}
        {props.SOC !== undefined && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Organic Carbon (%)</div>
            <div className="text-lg font-semibold text-gray-800">{props.SOC?.toFixed(2)}</div>
          </div>
        )}
        {props.Clay !== undefined && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-600">Clay (%)</div>
            <div className="text-lg font-semibold text-gray-800">{props.Clay?.toFixed(1)}</div>
          </div>
        )}
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
        <strong>Note:</strong> Soil data is estimated from models (SoilGrids/ISRIC), not lab measurements.
      </div>
    </div>
  );
}
