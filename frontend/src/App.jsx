import { useMemo, useState } from 'react';
import MapPicker from './components/MapPicker';
import LanguageSwitcher from './components/LanguageSwitcher';
import { getTranslation } from './hooks/useTranslation';
import {
  predictYield,
  getLocationInfo,
  getSoil,
  getWeather,
  getCropInfo,
  getDistricts,
  simulateWhatIf,
  recommendFertilizer,
  getIrrigationSchedule,
  getDiseaseRisk,
  calculateEconomics,
  getRotationSuggestions,
  askAgronomist,
  getNdviStatus,
  getServiceHealth,
  downloadReport,
  storageHelper,
} from './api/yieldApi';
import {
  MapPin, Navigation, Sprout, CloudSun, Droplets, FlaskConical, Bug,
  IndianRupee, ArrowRightLeft, Satellite, MessageCircle, FileText,
  RefreshCw, ChevronDown, ChevronUp, ShieldCheck, Activity, Leaf,
  Tractor, CircleHelp, Languages, CheckCircle2, AlertTriangle, XCircle
} from 'lucide-react';

const crops = [
  { id: 'Wheat', icon: '🌾', emoji: '🌾' },
  { id: 'Rice', icon: '🌿', emoji: '🌿' },
];

const stages = [
  { id: 'sowing', en: 'Sowing' },
  { id: 'midseason', en: 'Mid-season' },
  { id: 'preharvest', en: 'Pre-harvest' },
];

const irrigationTypes = ['Canal', 'Tube Well', 'Canal + Tube Well', 'Rainfed', 'Other'];

const mspFallback = { Wheat: 2585, Rice: 2441 };

function SectionTitle({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="section-icon"><Icon size={20} /></div>
      <div>
        <h2 className="text-lg font-extrabold text-slate-900">{title}</h2>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, helper, tone = 'green' }) {
  return (
    <div className={`stat-card tone-${tone}`}>
      <div className="flex items-start justify-between gap-3">
        <span className="stat-icon"><Icon size={19} /></span>
        <span className="text-xs font-semibold text-slate-500 text-right">{label}</span>
      </div>
      <div className="mt-3 text-2xl sm:text-3xl font-black text-slate-900">{value}</div>
      {helper && <div className="text-xs text-slate-500 mt-1">{helper}</div>}
    </div>
  );
}

function StatusPill({ status }) {
  const config = {
    ready: { cls: 'status-ready', icon: CheckCircle2, text: 'Ready' },
    warning: { cls: 'status-warning', icon: AlertTriangle, text: 'Needs attention' },
    offline: { cls: 'status-offline', icon: XCircle, text: 'Unavailable' },
  }[status] || { cls: 'status-warning', icon: AlertTriangle, text: 'Check' };
  const Icon = config.icon;
  return <span className={`status-pill ${config.cls}`}><Icon size={13} />{config.text}</span>;
}

export default function App() {
  const [crop, setCrop] = useState('Wheat');
  const [latitude, setLatitude] = useState(30.9);
  const [longitude, setLongitude] = useState(75.5);
  const [farmArea, setFarmArea] = useState(1);
  const [sowingDate, setSowingDate] = useState('');
  const [seedVariety, setSeedVariety] = useState('');
  const [previousCrop, setPreviousCrop] = useState('');
  const [irrigationType, setIrrigationType] = useState('');
  const [stage, setStage] = useState('sowing');
  const [pumpLpm, setPumpLpm] = useState('');
  const [soilInput, setSoilInput] = useState({ n: '', p: '', k: '', ph: '' });
  const [prices, setPrices] = useState({ current: '', future: '', storageCost: 0, loss: 0 });
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [modules, setModules] = useState({});
  const [locationInfo, setLocationInfo] = useState(null);
  const [error, setError] = useState('');
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en');

  const t = (key) => getTranslation(lang, key);

  const setLanguage = (next) => {
    setLang(next);
    localStorage.setItem('lang', next);
  };

  const handleMapClick = (lat, lon) => {
    setLatitude(Number(lat.toFixed(5)));
    setLongitude(Number(lon.toFixed(5)));
  };

  const loadModules = async (prediction, soil, weather) => {
    const payloadBase = {
      latitude, longitude, crop, stage,
      area_ha: farmArea,
      farm_area: farmArea,
      pump_lpm: pumpLpm ? Number(pumpLpm) : undefined,
    };
    const soilPayload = {
      P: soilInput.p ? Number(soilInput.p) : soil?.properties?.P,
      K: soilInput.k ? Number(soilInput.k) : soil?.properties?.K,
      N: soilInput.n ? Number(soilInput.n) : soil?.properties?.N,
      pH: soilInput.ph ? Number(soilInput.ph) : soil?.properties?.pH,
    };
    const production = Number(prediction?.predicted_yield || 0) * 10 * farmArea;

    const jobs = {
      fertilizer: recommendFertilizer({
        crop,
        soil: soilPayload,
        area_ha: farmArea,
        target_yield_t_ha: Number(prediction?.predicted_yield || 0),
        previous_crop: previousCrop || undefined,
      }),
      irrigation: getIrrigationSchedule({
        latitude, longitude, crop, stage, area_ha: farmArea,
        pump_lpm: pumpLpm ? Number(pumpLpm) : undefined,
      }),
      disease: getDiseaseRisk({ latitude, longitude, crop, stage }),
      economics: calculateEconomics({
        crop,
        area_ha: farmArea,
        predicted_yield_t_ha: Number(prediction?.predicted_yield || 0),
        sale_price_per_quintal: Number(prices.current || mspFallback[crop] || 0),
      }),
      rotation: getRotationSuggestions({ crop, water_available: irrigationType ? 'known' : 'normal' }),
      ndvi: getNdviStatus(latitude, longitude),
      services: getServiceHealth(),
      storage: storageHelper({
        crop,
        production_quintals: production,
        current_price_per_quintal: Number(prices.current || mspFallback[crop] || 0),
        expected_future_price_per_quintal: Number(prices.future || prices.current || mspFallback[crop] || 0),
        storage_cost_per_quintal: Number(prices.storageCost || 0),
        expected_loss_percent: Number(prices.loss || 0),
      }),
    };

    const entries = Object.entries(jobs);
    const settled = await Promise.allSettled(entries.map(([, promise]) => promise));
    const next = {};
    entries.forEach(([key], index) => {
      next[key] = settled[index].status === 'fulfilled'
        ? settled[index].value
        : { error: settled[index].reason?.message || 'Module unavailable' };
    });
    setModules(next);
  };

  const runAnalysis = async () => {
    setIsLoading(true);
    setError('');
    setResult(null);
    setModules({});
    setLocationInfo(null);

    try {
      const season = crop === 'Wheat' ? 'Rabi' : 'Kharif';
      const [location, weather, soil, prediction] = await Promise.all([
        getLocationInfo(latitude, longitude),
        getWeather(latitude, longitude, season),
        getSoil(latitude, longitude),
        predictYield({
          latitude, longitude, crop,
          seed_variety: seedVariety || undefined,
          sowing_date: sowingDate || undefined,
          farm_area: farmArea,
          stage,
          irrigation: irrigationType || undefined,
          previous_crop: previousCrop || undefined,
          soil_test_ph: soilInput.ph ? Number(soilInput.ph) : undefined,
          soil_test_n: soilInput.n ? Number(soilInput.n) : undefined,
        }),
      ]);
      setLocationInfo(location);
      setResult(prediction);
      await loadModules(prediction, soil, weather);
      setActiveTab('overview');
    } catch (err) {
      setError(err.message || 'Unable to analyze this field.');
    } finally {
      setIsLoading(false);
    }
  };

  const ask = async (question) => {
    try {
      const answer = await askAgronomist({
        question,
        crop,
        stage,
        latitude,
        longitude,
        prediction: result?.predicted_yield,
      });
      setModules((m) => ({ ...m, agronomist: answer }));
    } catch (err) {
      setModules((m) => ({ ...m, agronomist: { error: err.message } }));
    }
  };

  const reset = () => {
    setResult(null);
    setModules({});
    setError('');
    setLocationInfo(null);
    setActiveTab('overview');
  };

  const reliabilityTone = result?.reliability === 'High' ? 'green' : result?.reliability === 'Low' ? 'red' : 'amber';
  const productionQt = result ? Number(result.predicted_yield || 0) * 10 * farmArea : 0;
  const econ = modules.economics || {};
  const rotationItems = modules.rotation?.suggestions || modules.rotation?.options || [];
  const disease = modules.disease || {};
  const irrigationRows = modules.irrigation?.daily || modules.irrigation?.schedule || [];
  const fertilizer = modules.fertilizer || {};

  const quickPrompts = useMemo(() => (
    crop === 'Wheat'
      ? ['Should I irrigate today?', 'How much urea should I use?', 'Is yellow rust risk high?']
      : ['When should I irrigate?', 'How should I manage nitrogen?', 'What disease risk should I watch?']
  ), [crop]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand-wrap">
            <div className="brand-mark"><Sprout size={22} /></div>
            <div>
              <div className="brand-title">Kheti<span>AI</span></div>
              <div className="brand-subtitle">Punjab Farm Decision Dashboard</div>
            </div>
          </div>
          <div className="top-actions">
            <div className="market-chip"><IndianRupee size={14} /> MSP-aware tools</div>
            <LanguageSwitcher value={lang} onChange={setLanguage} />
          </div>
        </div>
      </header>

      <main className="dashboard">
        {!result ? (
          <>
            <section className="hero-card">
              <div className="hero-copy">
                <div className="eyebrow"><Tractor size={14} /> Built for Punjab farmers</div>
                <h1>Know your field. Plan your season.</h1>
                <p>Get your yield estimate, water plan, crop-risk signals and farm economics in one simple view.</p>
                <div className="hero-badges">
                  <span><CheckCircle2 size={14} /> Wheat & Rice</span>
                  <span><CloudSun size={14} /> Weather-aware</span>
                  <span><ShieldCheck size={14} /> Decision support</span>
                </div>
              </div>
              <div className="hero-graphic" aria-hidden="true">
                <div className="sun-orb"></div>
                <div className="field-lines"></div>
                <span className="crop-stem stem-1">🌾</span>
                <span className="crop-stem stem-2">🌾</span>
                <span className="crop-stem stem-3">🌿</span>
              </div>
            </section>

            <div className="grid lg:grid-cols-[1.05fr_.95fr] gap-6 mt-6">
              <section className="panel-card">
                <div className="step-row">
                  <span className="step-badge">1</span>
                  <div>
                    <h2>Tell us about your field</h2>
                    <p>Only the basics are needed. Advanced details can be added later.</p>
                  </div>
                </div>

                <div className="form-section">
                  <SectionTitle icon={Sprout} title="Choose your crop" subtitle="Select what is planted in this field." />
                  <div className="crop-grid">
                    {crops.map((c) => (
                      <button key={c.id} onClick={() => setCrop(c.id)} className={`crop-choice ${crop === c.id ? 'active' : ''}`}>
                        <span className="crop-emoji">{c.emoji}</span>
                        <span>{t(c.id === 'Wheat' ? 'wheat' : 'rice')}</span>
                        <span className="crop-check">{crop === c.id ? <CheckCircle2 size={17} /> : null}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="form-section">
                  <SectionTitle icon={MapPin} title="Where is the field?" subtitle="Use GPS or enter the location." />
                  <button className="gps-button" onClick={() => {
                    if (!navigator.geolocation) return setError('Location services are not supported on this device.');
                    navigator.geolocation.getCurrentPosition(
                      (pos) => handleMapClick(pos.coords.latitude, pos.coords.longitude),
                      (e) => setError(e.message || 'Could not read your location.'),
                      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
                    );
                  }}>
                    <Navigation size={18} /> Use my current location
                  </button>
                  <div className="coord-grid mt-3">
                    <label>Latitude<input type="number" step="any" value={latitude} onChange={(e) => setLatitude(Number(e.target.value))} /></label>
                    <label>Longitude<input type="number" step="any" value={longitude} onChange={(e) => setLongitude(Number(e.target.value))} /></label>
                  </div>
                  <div className="map-frame mt-3">
                    <MapPicker onLocationSelect={handleMapClick} position={[latitude, longitude]} />
                  </div>
                  {locationInfo && (
                    <div className="location-strip mt-3">
                      <MapPin size={16} /><strong>{locationInfo.district || 'Punjab'}</strong><span>•</span><span>{locationInfo.elevation_m ?? '—'} m elevation</span>
                    </div>
                  )}
                </div>

                <div className="form-section">
                  <SectionTitle icon={Activity} title="Field basics" />
                  <div className="form-grid">
                    <label>Farm area (hectares)<input type="number" min="0.1" step="0.1" value={farmArea} onChange={(e) => setFarmArea(Number(e.target.value))} /></label>
                    <label>Crop stage<select value={stage} onChange={(e) => setStage(e.target.value)}>{stages.map(s => <option key={s.id} value={s.id}>{s.en}</option>)}</select></label>
                    <label>Sowing date<input type="date" value={sowingDate} onChange={(e) => setSowingDate(e.target.value)} /></label>
                    <label>Irrigation type<select value={irrigationType} onChange={(e) => setIrrigationType(e.target.value)}><option value="">Select</option>{irrigationTypes.map(x => <option key={x}>{x}</option>)}</select></label>
                  </div>
                </div>

                <div className="advanced-box">
                  <button className="advanced-toggle" onClick={() => setAdvancedOpen(!advancedOpen)}>
                    <span><FlaskConical size={16} /> Add soil & farm details</span>{advancedOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </button>
                  {advancedOpen && (
                    <div className="advanced-grid mt-4">
                      <label>Seed variety<input value={seedVariety} onChange={(e) => setSeedVariety(e.target.value)} placeholder="e.g. PBW-550" /></label>
                      <label>Previous crop<input value={previousCrop} onChange={(e) => setPreviousCrop(e.target.value)} placeholder="e.g. Rice" /></label>
                      <label>Soil pH (lab)<input type="number" step="0.1" value={soilInput.ph} onChange={(e) => setSoilInput(s => ({...s, ph:e.target.value}))} placeholder="Optional" /></label>
                      <label>Nitrogen (kg/ha)<input type="number" value={soilInput.n} onChange={(e) => setSoilInput(s => ({...s, n:e.target.value}))} placeholder="Optional" /></label>
                      <label>Phosphorus (kg/ha)<input type="number" value={soilInput.p} onChange={(e) => setSoilInput(s => ({...s, p:e.target.value}))} placeholder="Optional" /></label>
                      <label>Potassium (kg/ha)<input type="number" value={soilInput.k} onChange={(e) => setSoilInput(s => ({...s, k:e.target.value}))} placeholder="Optional" /></label>
                      <label>Pump discharge (L/min)<input type="number" value={pumpLpm} onChange={(e) => setPumpLpm(e.target.value)} placeholder="Optional" /></label>
                    </div>
                  )}
                </div>

                <button className="primary-cta" onClick={runAnalysis} disabled={isLoading}>
                  {isLoading ? <><RefreshCw size={19} className="spin" /> Analyzing field…</> : <><Sprout size={19} /> Analyze my field</>}
                </button>
              </section>

              <section className="panel-card map-panel">
                <SectionTitle icon={MapPin} title="Your field location" subtitle="The map helps confirm that your coordinates are correct." />
                <div className="large-map-wrap">
                  <MapPicker onLocationSelect={handleMapClick} position={[latitude, longitude]} />
                </div>
                <div className="map-help">
                  <div className="help-icon"><CircleHelp size={18} /></div>
                  <div><strong>Tip:</strong> You can use your phone's location button or enter coordinates manually. Keep the marker inside Punjab.</div>
                </div>
                <div className="mini-source-row">
                  <span><Satellite size={15} /> Soil: modeled field estimate</span>
                  <span><CloudSun size={15} /> Weather: Open-Meteo</span>
                </div>
              </section>
            </div>
          </>
        ) : (
          <>
            <section className="result-hero">
              <div>
                <div className="eyebrow"><CheckCircle2 size={14} /> Field analysis complete</div>
                <h1>{result.crop} field in {result.district || locationInfo?.district || 'Punjab'}</h1>
                <p>Here is the action plan for this field. Start with the cards marked for today.</p>
              </div>
              <div className="result-actions">
                <button className="ghost-button" onClick={reset}><RefreshCw size={16} /> New analysis</button>
                <button className="download-button" onClick={() => downloadReport({
                  location: { district: result.district || locationInfo?.district, latitude, longitude },
                  crop, area_hectares: farmArea, prediction: result, fertilizer, irrigation: modules.irrigation, disease, economics: econ, rotation: rotationItems
                })}><FileText size={16} /> Field report</button>
              </div>
            </section>

            <div className="metrics-grid">
              <StatCard icon={Sprout} label="Predicted yield" value={`${Number(result.predicted_yield).toFixed(2)} t/ha`} helper={`${productionQt.toFixed(1)} quintals for this field`} />
              <StatCard icon={ShieldCheck} label="Reliability" value={result.reliability || 'Medium'} helper={`${Math.round((result.data_completeness || 0) * 100)}% data completeness`} tone={reliabilityTone} />
              <StatCard icon={IndianRupee} label="Reference price" value={`₹${Number(econ.price_per_quintal || mspFallback[crop] || 0).toLocaleString('en-IN')}/q`} helper="Use your local sale offer when known" tone="blue" />
              <StatCard icon={Droplets} label="Irrigation view" value={irrigationRows.length ? `${irrigationRows[0]?.irrigation_mm ?? 0} mm` : 'Ready'} helper="First forecast action" tone="amber" />
            </div>

            <div className="tab-bar">
              {[
                ['overview','Overview'],
                ['water','Water & risk'],
                ['money','Money & market'],
                ['soil','Soil & crop'],
                ['assistant','Farm assistant'],
              ].map(([id,label]) => <button key={id} className={activeTab===id?'active':''} onClick={()=>setActiveTab(id)}>{label}</button>)}
            </div>

            {activeTab === 'overview' && (
              <div className="results-grid">
                <section className="panel-card span-2">
                  <SectionTitle icon={Sprout} title="Yield snapshot" subtitle="Your estimate compared with the model's district reference." />
                  <div className="yield-layout">
                    <div className="yield-number">{Number(result.predicted_yield).toFixed(2)} <span>t/ha</span></div>
                    <div className="yield-details">
                      <div><span>District reference</span><strong>{Number(result.historical_baseline || 0).toFixed(2)} t/ha</strong></div>
                      <div><span>Prediction interval</span><strong>{result.prediction_interval?.lower ?? '—'}–{result.prediction_interval?.upper ?? '—'} t/ha</strong></div>
                      <div><span>Main drivers</span><strong>{result.important_features?.slice(0,2).map(x=>x.feature?.replaceAll('_',' ')).join(' • ') || 'Weather + soil'}</strong></div>
                    </div>
                  </div>
                  <div className="note-box"><ShieldCheck size={16} /><span>{result.explanation || 'Use this as a planning estimate, not a guaranteed harvest.'}</span></div>
                </section>

                <section className="panel-card">
                  <SectionTitle icon={FlaskConical} title="Fertilizer plan" subtitle="Use with your soil test and local agronomy guidance." />
                  {fertilizer.error ? <div className="empty-state">Fertilizer module unavailable.</div> : (
                    <div className="action-list">
                      {Object.entries(fertilizer.recommendations || fertilizer.plan || {}).slice(0,4).map(([k,v]) => (
                        <div key={k} className="action-row"><span>{k.replaceAll('_',' ')}</span><strong>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</strong></div>
                      ))}
                    </div>
                  )}
                </section>

                <section className="panel-card">
                  <SectionTitle icon={Droplets} title="Next water action" subtitle="Weather-aware estimate for the first forecast day." />
                  {irrigationRows[0] ? (
                    <div className="water-highlight"><div className="water-big">{irrigationRows[0].irrigation_mm ?? 0}<span> mm</span></div><p>{irrigationRows[0].date || 'Next forecast day'}</p>{irrigationRows[0].pump_runtime_min != null && <div className="runtime">≈ {irrigationRows[0].pump_runtime_min} min pump runtime</div>}</div>
                  ) : <div className="empty-state">Irrigation forecast not available.</div>}
                </section>

                <section className="panel-card">
                  <SectionTitle icon={Bug} title="Crop health watch" subtitle="Weather-based risk signal — not a diagnosis." />
                  {disease.error ? <div className="empty-state">Disease module unavailable.</div> : <div className={`risk-banner risk-${String(disease.risks?.[0]?.risk_levels?.[0]?.risk_level || 'medium').toLowerCase()}`}><div className="risk-score">{disease.risks?.[0]?.risk_score ?? '—'}</div><div><strong>{disease.risks?.[0]?.disease || disease.risk || 'Crop disease risk'}</strong><p>{disease.risks?.[0]?.why?.join(', ') || disease.disclaimer || 'Watch crop and field conditions closely.'}</p></div></div>}
                </section>

                <section className="panel-card">
                  <SectionTitle icon={IndianRupee} title="Farm money snapshot" subtitle="Gross-revenue scenario using the selected reference price." />
                  <div className="money-number">₹{Number(econ.gross_revenue || 0).toLocaleString('en-IN')}</div>
                  <div className="money-meta"><span>Production</span><strong>{productionQt.toFixed(1)} q</strong></div>
                  <div className="money-meta"><span>Reference price</span><strong>₹{Number(econ.price_per_quintal || mspFallback[crop] || 0).toLocaleString('en-IN')}/q</strong></div>
                </section>
              </div>
            )}

            {activeTab === 'water' && (
              <div className="results-grid">
                <section className="panel-card span-2">
                  <SectionTitle icon={Droplets} title="7-day irrigation scheduler" subtitle="Daily estimate based on ET0, crop stage and forecast weather." />
                  <div className="table-wrap"><table><thead><tr><th>Date</th><th>ET0</th><th>Rain</th><th>ETc</th><th>Irrigate</th><th>Pump</th></tr></thead><tbody>{irrigationRows.map((r,i)=><tr key={i}><td>{r.date || '—'}</td><td>{r.et0_mm ?? '—'} mm</td><td>{r.rain_mm ?? '—'} mm</td><td>{r.crop_et_mm ?? '—'} mm</td><td><strong>{r.irrigation_mm ?? 0} mm</strong></td><td>{r.pump_runtime_minutes != null ? `${r.pump_runtime_minutes} min` : 'Add pump flow'}</td></tr>)}</tbody></table></div>
                </section>
                <section className="panel-card span-2"><SectionTitle icon={Bug} title="Health warning" subtitle="Weather signal to help you inspect the field earlier." /><div className="risk-card"><div><div className="muted-label">Risk level</div><div className="risk-level-text">{disease.risk_level || '—'}</div></div><div><div className="muted-label">Signal</div><div>{disease.message || disease.risk || 'No warning available.'}</div></div></div></section>
              </div>
            )}

            {activeTab === 'money' && (
              <div className="results-grid">
                <section className="panel-card"><SectionTitle icon={IndianRupee} title="Revenue & MSP" /><div className="money-number">₹{Number(econ.gross_revenue || 0).toLocaleString('en-IN')}</div><p className="text-slate-500 mt-2">Reference price: ₹{Number(econ.price_per_quintal || mspFallback[crop] || 0).toLocaleString('en-IN')}/q</p></section>
                <section className="panel-card"><SectionTitle icon={ArrowRightLeft} title="Storage scenario" subtitle="Scenario calculator, not a market-price forecast." />{modules.storage?.error ? <div className="empty-state">Storage tool unavailable.</div> : <div className="storage-box"><div><span>Instant sale</span><strong>₹{Number(modules.storage?.instant_sale_value || 0).toLocaleString('en-IN')}</strong></div><div><span>After storage</span><strong>₹{Number(modules.storage?.storage_future_net_value || 0).toLocaleString('en-IN')}</strong></div><div><span>Break-even future price</span><strong>₹{Number(modules.storage?.break_even_future_price_per_quintal || 0).toLocaleString('en-IN')}/q</strong></div></div>}</section>
              </div>
            )}

            {activeTab === 'soil' && (
              <div className="results-grid">
                <section className="panel-card"><SectionTitle icon={FlaskConical} title="Soil profile" subtitle="Modeled data can support planning, but a lab test is better for fertilizer decisions." /><div className="soil-grid">{Object.entries(result.soil || modules.soil || {}).slice(0,8).map(([k,v])=><div className="soil-chip" key={k}><span>{k.replaceAll('_',' ')}</span><strong>{typeof v==='number'?v.toFixed(2):String(v)}</strong></div>)}</div></section>
                <section className="panel-card"><SectionTitle icon={Leaf} title="Rotation ideas" subtitle="Check local sowing window, water availability and market before changing a plan." /><div className="rotation-list">{rotationItems.map((item,i)=><div key={i} className="rotation-row"><div><strong>{item.crop || item.name || item}</strong><p>{item.reason || item.note || 'Potential rotation option'}</p></div><ArrowRightLeft size={17}/></div>)}</div></section>
              </div>
            )}

            {activeTab === 'assistant' && (
              <div className="results-grid">
                <section className="panel-card span-2">
                  <SectionTitle icon={MessageCircle} title="KhetiAI assistant" subtitle="Ask in your selected language. Current assistant uses the farm context available to the app." />
                  <div className="prompt-grid">{quickPrompts.map(q=><button key={q} className="prompt-chip" onClick={()=>ask(q)}>{q}</button>)}</div>
                  <div className="assistant-box"><div className="assistant-avatar"><MessageCircle size={19}/></div><div>{modules.agronomist?.answer || modules.agronomist?.response || 'Choose a question above to get a field-specific answer.'}</div></div>
                </section>
                <section className="panel-card"><SectionTitle icon={Satellite} title="Satellite view" subtitle="Live NDVI requires Copernicus credentials." /><StatusPill status={modules.ndvi?.available ? 'ready' : 'warning'} /><p className="text-slate-500 text-sm mt-3">{modules.ndvi?.message || 'NDVI status unavailable.'}</p></section>
                <section className="panel-card"><SectionTitle icon={Activity} title="Data services" subtitle="Quick health check for connected services." />{Object.entries(modules.services || {}).map(([k,v])=><div className="service-row" key={k}><span>{k.replaceAll('_',' ')}</span><StatusPill status={v ? 'ready' : 'offline'} /></div>)}</section>
              </div>
            )}
          </>
        )}

        {error && <div className="error-banner"><AlertTriangle size={18} /><div><strong>We could not complete the analysis.</strong><p>{error}</p></div><button onClick={runAnalysis}><RefreshCw size={16}/> Retry</button></div>}
      </main>

      <footer className="footer">
        <div><strong>KhetiAI</strong> • Punjab farmer decision support</div>
        <div>AI outputs are planning aids, not certified agronomic, financial or insurance advice.</div>
      </footer>
    </div>
  );
}
