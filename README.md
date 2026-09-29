# AI Crop Yield Predictor - Punjab
# Wheat & Rice | 3-Day Hackathon | Team of 4

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python train_model.py
uvicorn app:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Features
- 🌾 Crop yield prediction for Wheat & Rice (Punjab)
- 📍 Location-based data (GPS/Map/Manual)
- 🌤️ Weather integration (Open-Meteo)
- 🗺️ Soil data (SoilGrids)
- 📊 Historical baseline comparison
- 🎯 Prediction intervals & reliability scores
- 📱 Mobile-first responsive UI
- 🇮🇳 English | Hindi | ਪੰਜਾਬੀ
- 🔮 What-if simulation

## Architecture
- **ML**: LightGBM + Random Forest ensemble
- **Backend**: FastAPI (Python)
- **Frontend**: React + Tailwind CSS
- **Maps**: Leaflet
- **Data**: NASA POWER, SoilGrids, Open-Meteo, IMD

## Project Structure
```
├── backend/
│   ├── app.py              # FastAPI main
│   ├── model/
│   │   ├── predictor.py    # ML model wrapper
│   │   ├── train.py        # Training pipeline
│   │   └── features.py     # Feature engineering
│   ├── data/
│   │   ├── loader.py       # Data loading
│   │   └── cleaner.py      # Data cleaning
│   └── utils/
│       ├── weather.py      # Weather API
│       ├── soil.py         # Soil API
│       └── geo.py          # Geospatial utilities
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   └── public/
└── data/
    └── punjab_districts.geojson
```

## Data Sources
- Yield: data.gov.in (DES, Punjab)
- Weather: Open-Meteo (free, no key)
- Soil: SoilGrids (ISRIC, free)
- Geography: Punjab district boundaries

## Team
- Member 1: ML/Data
- Member 2: Geospatial/APIs
- Member 3: Frontend/UX
- Member 4: Backend/FastAPI

## License
Hackathon project - educational use
