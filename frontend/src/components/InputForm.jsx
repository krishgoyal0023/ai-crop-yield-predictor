import { useState, useEffect } from 'react';
import { translations } from '../hooks/useTranslation';

const CROPS = [
  { id: 'wheat', nameKey: 'wheat', icon: '🌾', color: 'wheat' },
  { id: 'rice', nameKey: 'rice', icon: '🌾', color: 'rice' },
];

const STAGES = [
  { id: 'sowing', nameKey: 'stages.sowing' },
  { id: 'midseason', nameKey: 'stages.midseason' },
  { id: 'preharvest', nameKey: 'stages.preharvest' },
];

const IRRIGATION_TYPES = [
  'Canal', 'Tube Well', 'Canal + Tube Well', 'Rainfed', 'Other'
];

export default function InputForm({
  crop, setCrop,
  latitude, setLatitude,
  longitude, setLongitude,
  farmArea, setFarmArea,
  sowingDate, setSowingDate,
  seedVariety, setSeedVariety,
  previousCrop, setPreviousCrop,
  irrigationType, setIrrigationType,
  stage, setStage,
  onPredict,
  isPredicting,
  showAdvanced,
  setShowAdvanced
}) {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en');
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsError, setGpsError] = useState(null);

  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === 'lang') setLang(e.newValue || 'en');
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const t = (key) => {
    const keys = key.split('.');
    let value = translations[lang];
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) value = value[k];
      else return key;
    }
    return typeof value === 'string' ? value : key;
  };

  const handleGetGPS = () => {
    setGpsLoading(true);
    setGpsError(null);

    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser');
      setGpsLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
        setGpsLoading(false);
      },
      (error) => {
        setGpsError(error.message);
        setGpsLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">
        {t('predict')}
      </h2>

      {/* Crop Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          {t('selectCrop')}
        </label>
        <div className="grid grid-cols-2 gap-3">
          {CROPS.map((c) => (
            <button
              key={c.id}
              onClick={() => setCrop(c.id === 'wheat' ? 'Wheat' : 'Rice')}
              className={`p-4 rounded-lg border-2 transition-all ${
                crop === (c.id === 'wheat' ? 'Wheat' : 'Rice')
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-3xl mb-2">{c.icon}</div>
              <div className="font-semibold text-gray-800">{t(c.nameKey)}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Location */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('farmLocation')}
        </label>
        <div className="space-y-3">
          <div className="flex gap-2">
            <button
              onClick={handleGetGPS}
              disabled={gpsLoading}
              className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors text-sm font-medium"
            >
              {gpsLoading ? '📍 Locating...' : t('useGPS')}
            </button>
          </div>

          {gpsError && (
            <div className="text-red-500 text-sm">{gpsError}</div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Latitude</label>
              <input
                type="number"
                step="any"
                value={latitude}
                onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="30.9"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Longitude</label>
              <input
                type="number"
                step="any"
                value={longitude}
                onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="75.5"
              />
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-800">
            <strong>Punjab bounds:</strong> Lat 29.5-32.5, Lon 73.5-76.8
          </div>
        </div>
      </div>

      {/* Farm Area */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('farmArea')}
        </label>
        <input
          type="number"
          step="0.1"
          min="0.1"
          value={farmArea}
          onChange={(e) => setFarmArea(parseFloat(e.target.value) || 1)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {/* Sowing Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('sowingDate')}
        </label>
        <input
          type="date"
          value={sowingDate}
          onChange={(e) => setSowingDate(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">
          Required for accurate growing degree day calculations
        </p>
      </div>

      {/* Stage */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Prediction Stage
        </label>
        <select
          value={stage}
          onChange={(e) => setStage(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
        >
          {STAGES.map(s => (
            <option key={s.id} value={s.id}>{t(s.nameKey)}</option>
          ))}
        </select>
      </div>

      {/* Advanced Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-green-600 text-sm font-medium hover:text-green-700"
      >
        {showAdvanced ? '▼' : '▶'} {t('advancedPanel')}
      </button>

      {/* Advanced Options */}
      {showAdvanced && (
        <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
          <div>
            <label className="block text-xs text-gray-600 mb-1">{t('seedVariety')}</label>
            <input
              type="text"
              value={seedVariety}
              onChange={(e) => setSeedVariety(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              placeholder="e.g., PBW-550"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-600 mb-1">{t('previousCrop')}</label>
            <select
              value={previousCrop}
              onChange={(e) => setPreviousCrop(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Select...</option>
              <option value="Wheat">Wheat</option>
              <option value="Rice">Rice</option>
              <option value="Cotton">Cotton</option>
              <option value="Maize">Maize</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-600 mb-1">{t('irrigationType')}</label>
            <select
              value={irrigationType}
              onChange={(e) => setIrrigationType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Select...</option>
              {IRRIGATION_TYPES.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Predict Button */}
      <button
        onClick={onPredict}
        disabled={isPredicting}
        className="w-full bg-green-600 text-white py-4 rounded-lg font-semibold text-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors shadow-lg"
      >
        {isPredicting ? (
          <span className="flex items-center justify-center gap-2">
            <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }}></div>
            {t('predicting')}
          </span>
        ) : (
          t('predictButton')
        )}
      </button>
    </div>
  );
}
