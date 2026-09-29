import { useState, useEffect } from 'react';
import MapPicker from './components/MapPicker';
import InputForm from './components/InputForm';
import PredictionResult from './components/PredictionResult';
import SoilCard from './components/SoilCard';
import WeatherCard from './components/WeatherCard';
import AdvancedPanel from './components/AdvancedPanel';
import LanguageSwitcher from './components/LanguageSwitcher';
import { predictYield, getLocationInfo, getSoil, getWeather } from './api/yieldApi';

export default function App() {
  const [crop, setCrop] = useState('Wheat');
  const [latitude, setLatitude] = useState(30.9);
  const [longitude, setLongitude] = useState(75.5);
  const [farmArea, setFarmArea] = useState(1.0);
  const [sowingDate, setSowingDate] = useState('');
  const [seedVariety, setSeedVariety] = useState('');
  const [previousCrop, setPreviousCrop] = useState('');
  const [irrigationType, setIrrigationType] = useState('');
  const [stage, setStage] = useState('sowing');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [isPredicting, setIsPredicting] = useState(false);
  const [result, setResult] = useState(null);
  const [soilData, setSoilData] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [error, setError] = useState(null);
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en');

  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === 'lang') setLang(e.newValue || 'en');
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const t = (key) => {
    const keys = key.split('.');
    let value = {
      en: {
        appName: 'AI Crop Yield Predictor',
        appSubtitle: 'Punjab Wheat & Rice',
        tagline: 'Smart predictions for better harvests',
        predict: 'Predict Yield',
        predicting: 'Predicting...',
        predictButton: 'Predict Yield',
        advancedPanel: 'Advanced Options',
        disclaimer: 'This is a model simulation. Actual yields may vary.',
        home: 'Home',
      },
      hi: {
        appName: 'AI फसल उपज पूर्वानुमान',
        appSubtitle: 'पंजाब गेहूं और चावल',
        tagline: 'बेहतर कटाई के लिए स्मार्ट पूर्वानुमान',
        predict: 'उपज पूर्वानुमान',
        predicting: 'पूर्वानुमान हो रहा है...',
        predictButton: 'उपज पूर्वानुमान लगाएं',
        advancedPanel: 'उन्नत विकल्प',
        disclaimer: 'यह एक मॉडел अनुकरण है। वास्तविक उपज भिन्न हो सकती है।',
        home: 'होम',
      },
      pa: {
        appName: 'AI ਫਸਲ ਉਪਜ ਪੂਰਵਾਨੁਮਾਨ',
        appSubtitle: 'ਪੰਜਾਬ ਗੇਹੂੰ ਅਤੇ ਚਾਵਲ',
        tagline: 'ਬਿਹਤਰ ਕਟਾਈ ਲਈ ਸਮਾਰਟ ਪੂਰਵਾਨੁਮਾਨ',
        predict: 'ਉਪਜ ਪੂਰਵਾਨੁਮਾਨ',
        predicting: 'ਪੂਰਵਾਨੁਮਾਨ ਹੋ ਰਿਹਾ ਹੈ...',
        predictButton: 'ਉਪਜ ਪੂਰਵਾਨੁਮਾਨ ਕਰੋ',
        advancedPanel: 'ਉੱਚਨਤ ਵਿਕਲਪ',
        disclaimer: 'ਇਹ ਮਾਡਲ ਸਿਮੂਲੇਸ਼ਨ ਹੈ। ਅਸਲ ਉਪਜ ਵੱਖਰੀ ਹੋ ਸਕਦੀ ਹੈ।',
        home: 'ਹੋਮ',
      },
    }[lang] || {};
    const k = key.split('.');
    let v = value;
    for (const key of k) { if (v && typeof v === 'object' && key in v) v = v[key]; else return key; }
    return typeof v === 'string' ? v : key;
  };

  const handleMapClick = (lat, lon) => {
    setLatitude(lat);
    setLongitude(lon);
  };

  const handlePredict = async () => {
    setIsPredicting(true);
    setError(null);
    setResult(null);

    try {
      // Fetch weather and soil data in parallel
      const season = crop === 'Wheat' ? 'Rabi' : 'Kharif';
      const [weather, soil] = await Promise.all([
        getWeather(latitude, longitude, season).catch(() => null),
        getSoil(latitude, longitude).catch(() => null),
      ]);

      setWeatherData(weather);
      setSoilData(soil);

      // Make prediction
      const prediction = await predictYield({
        latitude,
        longitude,
        crop,
        seed_variety: seedVariety || undefined,
        sowing_date: sowingDate || undefined,
        farm_area: farmArea,
        stage,
        irrigation: irrigationType || undefined,
        previous_crop: previousCrop || undefined,
      });

      setResult(prediction);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsPredicting(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setSoilData(null);
    setWeatherData(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50">
      {/* Header */}
      <header className="bg-green-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold">{t('appName')}</h1>
              <p className="text-green-100 text-sm md:text-base">{t('appSubtitle')} | {t('tagline')}</p>
            </div>
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {!result ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Input */}
            <div>
              <InputForm
                crop={crop}
                setCrop={setCrop}
                latitude={latitude}
                setLatitude={setLatitude}
                longitude={longitude}
                setLongitude={setLongitude}
                farmArea={farmArea}
                setFarmArea={setFarmArea}
                sowingDate={sowingDate}
                setSowingDate={setSowingDate}
                seedVariety={seedVariety}
                setSeedVariety={setSeedVariety}
                previousCrop={previousCrop}
                setPreviousCrop={setPreviousCrop}
                irrigationType={irrigationType}
                setIrrigationType={setIrrigationType}
                stage={stage}
                setStage={setStage}
                onPredict={handlePredict}
                isPredicting={isPredicting}
                showAdvanced={showAdvanced}
                setShowAdvanced={setShowAdvanced}
              />
            </div>

            {/* Right Column - Map & Data */}
            <div className="space-y-4">
              <div className="bg-white rounded-xl shadow-lg p-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Select Location</h3>
                <MapPicker
                  onLocationSelect={handleMapClick}
                  position={[latitude, longitude]}
                />
              </div>

              {soilData && <SoilCard soilData={soilData} />}
              {weatherData && <WeatherCard weatherData={weatherData} />}
            </div>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto">
            <PredictionResult result={result} onReset={handleReset} />
          </div>
        )}

        {/* Advanced Panel */}
        <AdvancedPanel
          showAdvanced={showAdvanced}
          onClose={() => setShowAdvanced(false)}
          onApply={handlePredict}
        />
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-300 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-sm mb-2">
            AI Crop Yield Predictor | Punjab Pilot: Wheat & Rice
          </p>
          <p className="text-xs text-gray-400">
            {t('disclaimer')}
          </p>
          <p className="text-xs text-gray-500 mt-4">
            Built for Hackathon | Data sources: Open-Meteo, SoilGrids (ISRIC)
          </p>
        </div>
      </footer>
    </div>
  );
}
