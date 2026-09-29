const API_BASE = '/api';

export async function predictYield(request) {
  const response = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Prediction failed');
  }
  return response.json();
}

export async function getLocationInfo(lat, lon) {
  const response = await fetch(`${API_BASE}/location`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude: lat, longitude: lon }),
  });
  if (!response.ok) throw new Error('Location lookup failed');
  return response.json();
}

export async function getWeather(lat, lon, season = 'Rabi') {
  const response = await fetch(`${API_BASE}/weather/${lat}/${lon}?season=${season}`);
  if (!response.ok) throw new Error('Weather fetch failed');
  return response.json();
}

export async function getSoil(lat, lon) {
  const response = await fetch(`${API_BASE}/soil/${lat}/${lon}`);
  if (!response.ok) throw new Error('Soil fetch failed');
  return response.json();
}

export async function getCropInfo(crop) {
  const response = await fetch(`${API_BASE}/crop-information/${crop}`);
  if (!response.ok) throw new Error('Crop info not found');
  return response.json();
}

export async function getDistricts() {
  const response = await fetch(`${API_BASE}/districts`);
  if (!response.ok) throw new Error('Failed to fetch districts');
  return response.json();
}

export async function simulateWhatIf(request) {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Simulation failed');
  }
  return response.json();
}


export async function chatWithAgronomist(request) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    let detail = 'Chat assistant is unavailable';
    try {
      const error = await response.json();
      detail = error.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return response.json();
}
