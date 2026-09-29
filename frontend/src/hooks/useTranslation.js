import { useState } from 'react';

const common = {
  en: { wheat:'Wheat', rice:'Rice', selectCrop:'Select crop', farmLocation:'Farm location', useGPS:'Use my location', farmArea:'Farm area (hectares)', sowingDate:'Sowing date', seedVariety:'Seed variety', previousCrop:'Previous crop', irrigationType:'Irrigation type', predictButton:'Analyze my field', predicting:'Analyzing…', stages:{sowing:'Sowing',midseason:'Mid-season',preharvest:'Pre-harvest'} },
  hi: { wheat:'गेहूं', rice:'चावल', selectCrop:'फसल चुनें', farmLocation:'खेत का स्थान', useGPS:'मेरा स्थान उपयोग करें', farmArea:'खेत का क्षेत्रफल (हेक्टेयर)', sowingDate:'बुवाई की तारीख', seedVariety:'बीज की किस्म', previousCrop:'पिछली फसल', irrigationType:'सिंचाई का प्रकार', predictButton:'मेरे खेत का विश्लेषण करें', predicting:'विश्लेषण हो रहा है…', stages:{sowing:'बुवाई',midseason:'मध्य मौसम',preharvest:'कटाई से पहले'} },
  pa: { wheat:'ਗੇਹੂੰ', rice:'ਚਾਵਲ', selectCrop:'ਫਸਲ ਚੁਣੋ', farmLocation:'ਖੇਤ ਦਾ ਟਿਕਾਣਾ', useGPS:'ਮੇਰੀ ਥਾਂ ਵਰਤੋ', farmArea:'ਖੇਤ ਦਾ ਰਕਬਾ (ਹੈਕਟੇਅਰ)', sowingDate:'ਬਿਜਾਈ ਦੀ ਤਾਰੀਖ', seedVariety:'ਬੀਜ ਦੀ ਕਿਸਮ', previousCrop:'ਪਿਛਲੀ ਫਸਲ', irrigationType:'ਸਿੰਚਾਈ ਦੀ ਕਿਸਮ', predictButton:'ਮੇਰੇ ਖੇਤ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰੋ', predicting:'ਵਿਸ਼ਲੇਸ਼ਣ ਹੋ ਰਿਹਾ ਹੈ…', stages:{sowing:'ਬਿਜਾਈ',midseason:'ਮੱਧ ਮੌਸਮ',preharvest:'ਵਾਢੀ ਤੋਂ ਪਹਿਲਾਂ'} },
};

export const translations = common;
export function getTranslation(lang,key){ const keys=key.split('.'); let v=translations[lang]||translations.en; for(const k of keys){ if(v&&typeof v==='object'&&k in v)v=v[k]; else return key; } return typeof v==='string'?v:key; }
export function useTranslation(){ const [lang,setLang]=useState(()=>localStorage.getItem('lang')||'en'); const t=(key)=>getTranslation(lang,key); const changeLang=(l)=>{setLang(l);localStorage.setItem('lang',l);}; return {lang,t,changeLang}; }
