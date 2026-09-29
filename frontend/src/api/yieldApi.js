const API_BASE = '/api';

async function request(path, options={}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {'Content-Type':'application/json', ...(options.headers||{})},
  });
  let body = null;
  try { body = await response.json(); } catch {}
  if (!response.ok) throw new Error(body?.detail || `Request failed (${response.status})`);
  return body;
}

export const predictYield = (data) => request('/predict',{method:'POST',body:JSON.stringify(data)});
export const getLocationInfo = (lat,lon) => request('/location',{method:'POST',body:JSON.stringify({latitude:lat,longitude:lon})});
export const getWeather = (lat,lon,season='Rabi') => request(`/weather/${lat}/${lon}?season=${season}`);
export const getSoil = (lat,lon) => request(`/soil/${lat}/${lon}`);
export const getCropInfo = (crop) => request(`/crop-information/${crop}`);
export const getDistricts = () => request('/districts');
export const simulateWhatIf = (data) => request('/simulate',{method:'POST',body:JSON.stringify(data)});
export const recommendFertilizer = (data) => request('/fertilizer/recommend',{method:'POST',body:JSON.stringify(data)});
export const getIrrigationSchedule = (data) => request('/irrigation/schedule',{method:'POST',body:JSON.stringify(data)});
export const getDiseaseRisk = (data) => request('/disease/risk',{method:'POST',body:JSON.stringify(data)});
export const calculateEconomics = (data) => request('/economics/calculate',{method:'POST',body:JSON.stringify(data)});
export const getRotationSuggestions = (data) => request('/rotation/suggestions',{method:'POST',body:JSON.stringify(data)});
export const askAgronomist = (data) => request('/agronomist',{method:'POST',body:JSON.stringify(data)});
export const getNdviStatus = () => request('/ndvi/status');
export const getServiceHealth = () => request('/health/services');

export async function downloadReport(payload){ const response=await fetch(`${API_BASE}/report`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); if(!response.ok) throw new Error('Report generation failed'); const blob=await response.blob(); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='field-assessment.pdf'; a.click(); URL.revokeObjectURL(url); }
