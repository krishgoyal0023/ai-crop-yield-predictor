const API_BASE = '/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = 'Request failed';
    try { const body = await response.json(); detail = body.detail || detail; } catch {}
    throw new Error(detail);
  }
  return response;
}
async function json(path, options) { return (await request(path, options)).json(); }

export async function predictYield(requestBody) { return json('/predict', { method:'POST', body:JSON.stringify(requestBody) }); }
export async function getLocationInfo(lat, lon) { return json('/location', { method:'POST', body:JSON.stringify({latitude:lat, longitude:lon}) }); }
export async function getWeather(lat, lon, season='Rabi') { return json(`/weather/${lat}/${lon}?season=${season}`); }
export async function getSoil(lat, lon) { return json(`/soil/${lat}/${lon}`); }
export async function getCropInfo(crop) { return json(`/crop-information/${crop}`); }
export async function getDistricts() { return json('/districts'); }
export async function simulateWhatIf(requestBody) { return json('/simulate', { method:'POST', body:JSON.stringify(requestBody) }); }
export async function recommendFertilizer(requestBody) { return json('/fertilizer/recommend', {method:'POST', body:JSON.stringify(requestBody)}); }
export async function getIrrigationSchedule(requestBody) { return json('/irrigation/schedule', {method:'POST', body:JSON.stringify(requestBody)}); }
export async function getDiseaseRisk(requestBody) { return json('/disease/risk', {method:'POST', body:JSON.stringify(requestBody)}); }
export async function calculateEconomics(requestBody) { return json('/economics/calculate', {method:'POST', body:JSON.stringify(requestBody)}); }
export async function getRotationSuggestions(requestBody) { return json('/rotation/suggestions', {method:'POST', body:JSON.stringify(requestBody)}); }
export async function askAgronomist(requestBody) { return json('/agronomist', {method:'POST', body:JSON.stringify(requestBody)}); }
export async function getNdviStatus(lat, lon) { return json(`/ndvi/status?latitude=${lat}&longitude=${lon}`); }
export async function getServiceHealth() { return json('/health/services'); }
export async function storageHelper(requestBody) { return json('/economics/storage', {method:'POST', body:JSON.stringify(requestBody)}); }

export async function downloadReport(reportPayload) {
  const response = await request('/report', {method:'POST', body:JSON.stringify(reportPayload)});
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'khetiai-field-assessment.pdf';
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}
