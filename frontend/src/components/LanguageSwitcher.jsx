import React, { useState } from 'react';
import { translations } from '../hooks/useTranslation';

export default function LanguageSwitcher() {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en');

  const languages = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
    { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
  ];

  return (
    <div className="flex gap-2">
      {languages.map((l) => (
        <button
          key={l.code}
          onClick={() => {
            setLang(l.code);
            localStorage.setItem('lang', l.code);
            window.location.reload();
          }}
          className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
            lang === l.code
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          title={l.name}
        >
          {l.flag}
        </button>
      ))}
    </div>
  );
}
