import { useState } from 'react';
import MapPicker from './components/MapPicker';
import {
  predictYield, getSoil, getWeather, recommendFertilizer,
  getIrrigationSchedule, getDiseaseRisk, calculateEconomics,
  getRotationSuggestions, askAgronomist, getNdviStatus, downloadReport, storageHelper
} from './api/yieldApi';

const Card=({title,children})=><section className="bg-white rounded-2xl shadow p-5 border border-gray-100"><h2 className="text-lg font-bold text-gray-800 mb-3">{title}</h2>{children}</section>;
const Stat=({label,value})=><div className="bg-gray-50 rounded-xl p-3"><div className="text-xs text-gray-500">{label}</div><div className="font-bold text-gray-800 mt-1">{value}</div></div>;

export default function App(){
  const [crop,setCrop]=useState('Wheat'),[lat,setLat]=useState(30.901),[lon,setLon]=useState(75.857);
  const [area,setArea]=useState(1),[stage,setStage]=useState('sowing'),[previousCrop,setPreviousCrop]=useState('');
  const [pump,setPump]=useState(''),[currentPrice,setCurrentPrice]=useState(''),[futurePrice,setFuturePrice]=useState(''),[storageCost,setStorageCost]=useState(''),[lossPct,setLossPct]=useState(''),[soilN,setSoilN]=useState(''),[soilP,setSoilP]=useState(''),[soilK,setSoilK]=useState('');
  const [loading,setLoading]=useState(false),[error,setError]=useState(''),[data,setData]=useState(null);
  const [question,setQuestion]=useState(''),[chat,setChat]=useState(null);

  const analyze=async()=>{
    setLoading(true);setError('');setData(null);
    try{
      const season=crop==='Wheat'?'Rabi':'Kharif';
      const [soil,weather,prediction]=await Promise.all([getSoil(lat,lon),getWeather(lat,lon,season),predictYield({
        latitude:lat,longitude:lon,crop,farm_area:area,stage,previous_crop:previousCrop||undefined
      })]);
      const soilProps=soil?.properties||{};
      const soilInput={...soilProps};
      if(soilN!=='') soilInput.N=Number(soilN);
      if(soilP!=='') soilInput.P=Number(soilP);
      if(soilK!=='') soilInput.K=Number(soilK);
      const [fert,irr,disease,econ,rotation,ndvi,storage]=await Promise.allSettled([
        recommendFertilizer({crop,soil:soilInput,area_ha:area,previous_crop:previousCrop||undefined}),
        getIrrigationSchedule({latitude:lat,longitude:lon,crop,stage,area_ha:area,pump_lpm:pump?Number(pump):undefined}),
        getDiseaseRisk({latitude:lat,longitude:lon,crop,stage}),
        calculateEconomics({crop,predicted_yield_t_ha:Number(prediction.predicted_yield)||0,area_ha:area}),
        getRotationSuggestions({crop,water_available:'normal'}),
        getNdviStatus()
      ]);
      const unwrap=x=>x.status==='fulfilled'?x.value:{error:x.reason?.message||'Module unavailable'};
      setData({soil,weather,prediction,fert:unwrap(fert),irr:unwrap(irr),disease:unwrap(disease),econ:unwrap(econ),rotation:unwrap(rotation),ndvi:unwrap(ndvi),storage:unwrap(storage)});
    }catch(e){setError(e.message||'Analysis failed');}
    finally{setLoading(false);}
  };

  const ask=async()=>{
    if(!question.trim()) return;
    try{setChat(await askAgronomist({question,crop,stage,soil:data?.soil?.properties||{},weather:data?.weather||{}}));}
    catch(e){setChat({answer:e.message});}
  };

  const reset=()=>{setData(null);setError('');setChat(null);};
  const report=async()=>{try{await downloadReport({location:{latitude:lat,longitude:lon},district:data.prediction.district,crop,area_ha:area,prediction:data.prediction,fertilizer:data.fert,irrigation:data.irr,disease:data.disease,economics:data.econ,rotation:data.rotation});}catch(e){setError(e.message);}};

  return <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50">
    <header className="bg-green-700 text-white shadow-lg"><div className="max-w-7xl mx-auto px-4 py-5">
      <div className="flex flex-col md:flex-row md:justify-between gap-2"><div><h1 className="text-3xl font-bold">AI Crop Yield Predictor</h1><p className="text-green-100">Punjab Farm Intelligence Dashboard</p></div>
      <div className="text-sm bg-green-800 rounded-lg px-3 py-2 self-start">Wheat • Rice • Soil • Weather • Water • Market</div></div>
    </div></header>

    <main className="max-w-7xl mx-auto p-4 md:p-6 space-y-5">
      {!data ? <div className="grid lg:grid-cols-2 gap-5">
        <Card title="Analyze Your Field">
          <div className="grid sm:grid-cols-2 gap-3">
            <label className="text-sm">Crop<select className="input mt-1 w-full border rounded-lg p-2" value={crop} onChange={e=>setCrop(e.target.value)}><option>Wheat</option><option>Rice</option></select></label>
            <label className="text-sm">Farm area (hectares)<input className="mt-1 w-full border rounded-lg p-2" type="number" min="0.1" step="0.1" value={area} onChange={e=>setArea(Number(e.target.value))}/></label>
            <label className="text-sm">Latitude<input className="mt-1 w-full border rounded-lg p-2" type="number" step="0.0001" value={lat} onChange={e=>setLat(Number(e.target.value))}/></label>
            <label className="text-sm">Longitude<input className="mt-1 w-full border rounded-lg p-2" type="number" step="0.0001" value={lon} onChange={e=>setLon(Number(e.target.value))}/></label>
            <label className="text-sm">Crop stage<select className="mt-1 w-full border rounded-lg p-2" value={stage} onChange={e=>setStage(e.target.value)}><option value="sowing">Sowing</option><option value="tillering">Tillering</option><option value="midseason">Mid-season</option><option value="flowering">Flowering</option><option value="grain_fill">Grain fill</option><option value="preharvest">Pre-harvest</option></select></label>
            <label className="text-sm">Previous crop<input className="mt-1 w-full border rounded-lg p-2" placeholder="e.g. Rice" value={previousCrop} onChange={e=>setPreviousCrop(e.target.value)}/></label>
            <label className="text-sm">Soil N (optional)<input className="mt-1 w-full border rounded-lg p-2" placeholder="kg/acre" value={soilN} onChange={e=>setSoilN(e.target.value)}/></label>
            <label className="text-sm">Soil P (optional)<input className="mt-1 w-full border rounded-lg p-2" placeholder="kg/acre" value={soilP} onChange={e=>setSoilP(e.target.value)}/></label>
            <label className="text-sm">Soil K (optional)<input className="mt-1 w-full border rounded-lg p-2" placeholder="kg/acre" value={soilK} onChange={e=>setSoilK(e.target.value)}/></label>
            <label className="text-sm">Pump discharge (optional)<input className="mt-1 w-full border rounded-lg p-2" placeholder="litres/min" value={pump} onChange={e=>setPump(e.target.value)}/></label><label className="text-sm">Current sale price<input className="mt-1 w-full border rounded-lg p-2" placeholder="₹/quintal" value={currentPrice} onChange={e=>setCurrentPrice(e.target.value)}/></label><label className="text-sm">Expected future price<input className="mt-1 w-full border rounded-lg p-2" placeholder="₹/quintal" value={futurePrice} onChange={e=>setFuturePrice(e.target.value)}/></label><label className="text-sm">Storage cost<input className="mt-1 w-full border rounded-lg p-2" placeholder="₹/quintal" value={storageCost} onChange={e=>setStorageCost(e.target.value)}/></label><label className="text-sm">Expected storage loss %<input className="mt-1 w-full border rounded-lg p-2" type="number" min="0" max="100" step="0.1" value={lossPct} onChange={e=>setLossPct(e.target.value)}/></label>
          </div>
          <button onClick={analyze} disabled={loading} className="mt-5 w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-3 rounded-xl">{loading?'Analyzing field...':'Analyze Field'}</button>
          {error&&<div className="mt-3 bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 text-sm">{error}</div>}
        </Card>
        <Card title="Select Field Location"><MapPicker onLocationSelect={(a,b)=>{setLat(a);setLon(b)}} position={[lat,lon]}/><p className="text-xs text-gray-500 mt-2">Click the map to update coordinates. Punjab coordinates are validated by the backend.</p></Card>
      </div>:
      <div className="space-y-5">
        <div className="flex justify-between items-center"><div><h2 className="text-2xl font-bold">Field Assessment</h2><p className="text-gray-500">{data.prediction.district} • {crop} • {area} ha</p></div><div className="flex gap-2"><button onClick={report} className="bg-green-600 text-white px-4 py-2 rounded-lg">PDF Report</button><button onClick={reset} className="border px-4 py-2 rounded-lg">New Analysis</button></div></div>

        <div className="grid md:grid-cols-4 gap-3">
          <Stat label="Predicted yield" value={`${data.prediction.predicted_yield} t/ha`}/><Stat label="Reliability" value={data.prediction.reliability}/><Stat label="Soil source" value={data.soil.source}/><Stat label="Weather source" value={data.weather.source}/>
        </div>

        <div className="grid lg:grid-cols-2 gap-5">
          <Card title="🌱 Soil"><div className="grid grid-cols-3 gap-3">{['pH','N','P','K','Clay','SOC'].map(k=><Stat key={k} label={k} value={data.soil.properties?.[k]??'—'}/>)}</div><p className="text-xs text-gray-500 mt-3">Remote soil values are estimates; lab results can be entered above on the next analysis.</p></Card>
          <Card title="🌦️ Weather"><div className="grid grid-cols-2 gap-3">{Object.entries(data.weather.features||{}).slice(0,6).map(([k,v])=><Stat key={k} label={k.replaceAll('_',' ')} value={typeof v==='number'?v.toFixed(1):v}/>)}</div></Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-5">
          <Card title="🧪 Fertilizer Plan"><pre className="whitespace-pre-wrap text-sm">{JSON.stringify(data.fert,null,2)}</pre></Card>
          <Card title="💧 7-Day Irrigation"><div className="overflow-auto"><table className="w-full text-sm"><thead><tr><th className="text-left">Date</th><th>ET0</th><th>Rain</th><th>Net mm</th><th>m³</th></tr></thead><tbody>{(data.irr.schedule||[]).map(r=><tr key={r.date} className="border-t"><td>{r.date}</td><td className="text-center">{r.et0_mm}</td><td className="text-center">{r.rain_mm}</td><td className="text-center font-bold">{r.irrigation_mm}</td><td className="text-center">{r.water_m3}</td></tr>)}</tbody></table></div>{data.irr.error&&<p>{data.irr.error}</p>}</Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-5">
          <Card title="🦠 Disease Early Warning"><div className="space-y-2">{(data.disease.risks||[]).map(r=><div key={r.date} className="border rounded-lg p-2 flex justify-between"><span>{r.date}</span><b>{r.disease}: {r.risk_level}</b></div>)}</div><p className="text-xs text-gray-500 mt-3">{data.disease.disclaimer}</p></Card>
          <Card title="💰 Revenue, MSP & Storage">{data.econ.error?<p className="text-sm text-red-600">{data.econ.error}</p>:<><div className="grid grid-cols-2 gap-2"><Stat label="Production" value={`${data.econ.production_quintals} q`}/><Stat label="Price" value={`₹${data.econ.price_per_quintal}/q`}/><Stat label="Revenue" value={`₹${Number(data.econ.gross_revenue||0).toLocaleString()}`}/><Stat label="Net before costs" value={`₹${Number(data.econ.net_profit||0).toLocaleString()}`}/></div><p className="text-xs text-gray-500 mt-3">MSP is a reference price; actual sale price can be entered in the input form.</p>{data.storage.error?<p className="text-xs text-red-600 mt-2">{data.storage.error}</p>:<div className="mt-3 border-t pt-3 text-sm">Storage scenario difference: <b>₹{Number(data.storage.difference||0).toLocaleString()}</b><br/>Break-even future price: <b>₹{data.storage.break_even_future_price_per_quintal??"—"}/q</b></div>}</>}</Card>
          <Card title="🔄 Rotation Options"><div className="space-y-2">{(data.rotation.alternatives||[]).map(x=><div className="border rounded-lg p-3" key={x.crop}><b>{x.crop}</b><p className="text-sm text-gray-600">{x.reason}</p></div>)}</div></Card>
        </div>

        <Card title="🛰️ Satellite NDVI"><div className="p-4 bg-gray-50 rounded-xl"><b>{data.ndvi.available?'Live NDVI available':'Live NDVI not connected yet'}</b><p className="text-sm text-gray-600 mt-1">{data.ndvi.message}</p><p className="text-xs mt-2">The implementation is intentionally not showing fabricated satellite values.</p></div></Card>

        <Card title="🤖 AI Agronomist"><div className="flex gap-2"><input className="flex-1 border rounded-lg p-3" placeholder="Ask about fertilizer, water, disease, MSP..." value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>e.key==='Enter'&&ask()}/><button onClick={ask} className="bg-green-600 text-white px-5 rounded-lg">Ask</button></div>{chat&&<div className="mt-3 bg-green-50 rounded-xl p-4 text-sm"><p>{chat.answer}</p><p className="text-xs text-gray-500 mt-2">Current assistant uses a deterministic agronomy rules layer. An external LLM/RAG provider can be connected in the next phase.</p></div>}</Card>
      </div>}
    </main>
    <footer className="text-center text-xs text-gray-500 py-8">Decision-support prototype • Verify field actions with current PAU/extension guidance and local soil observations.</footer>
  </div>
}
