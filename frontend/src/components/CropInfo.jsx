import { useState, useEffect } from 'react';
import { getCropInfo } from '../api/yieldApi';
import { translations } from '../hooks/useTranslation';

export default function CropInfo({ crop, onClose }) {
  const [info, setInfo] = useState(null);
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en');

  useEffect(() => {
    getCropInfo(crop).then(setInfo).catch(console.error);
  }, [crop]);

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

  if (!info) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-2xl font-bold text-gray-800">{info.name}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-700 mb-1">Season</h3>
            <p className="text-gray-600">{info.season}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <h3 className="font-semibold text-gray-700 mb-1">Sowing</h3>
              <p className="text-gray-600 text-sm">{info.sowing_months}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-1">Harvest</h3>
              <p className="text-gray-600 text-sm">{info.harvest_months}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 mb-1">Optimal pH</h3>
            <p className="text-gray-600">{info.optimal_ph}</p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 mb-1">Optimal Temperature</h3>
            <p className="text-gray-600">{info.optimal_temperature}</p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 mb-1">Water Requirement</h3>
            <p className="text-gray-600">{info.water_requirement}</p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 mb-2">Major Varieties in Punjab</h3>
            <div className="flex flex-wrap gap-2">
              {info.major_varieties_punjab.map((variety, idx) => (
                <span key={idx} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                  {variety}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 mb-1">Average Yield in Punjab</h3>
            <p className="text-gray-600">{info.average_yield_punjab}</p>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700">
            {info.description}
          </div>
        </div>
      </div>
    </div>
  );
}
