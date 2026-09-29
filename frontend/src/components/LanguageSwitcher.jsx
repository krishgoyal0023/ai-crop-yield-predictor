import { Globe2 } from 'lucide-react';

export default function LanguageSwitcher({ value, onChange }) {
  const languages = [
    { code:'en', label:'English' },
    { code:'hi', label:'हिन्दी' },
    { code:'pa', label:'ਪੰਜਾਬੀ' },
  ];
  return (
    <div className="language-switcher" aria-label="Language">
      <Globe2 size={15} />
      <select value={value} onChange={(e)=>onChange(e.target.value)} aria-label="Choose language">
        {languages.map(l=><option key={l.code} value={l.code}>{l.label}</option>)}
      </select>
    </div>
  );
}
