<div align="center">

# 🌾 AI Crop Yield Predictor 

**An End-to-End Machine Learning Platform for District-Level Yield Forecasting, Geospatial Soil Analytics, and Climate Sensitivity Simulation**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.3.0-38B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[🌐 Explore Repository](https://github.com/krishgoyal0023/ai-crop-yield-predictor) · [🐞 Report Bug](https://github.com/krishgoyal0023/ai-crop-yield-predictor/issues) · [💡 Request Feature](https://github.com/krishgoyal0023/ai-crop-yield-predictor/issues)

</div>

---

## 📌 Executive Summary

The **AI Crop Yield Predictor** is a specialized decision-support framework engineered to address agricultural volatility across **Punjab, India**. Designed specifically for the state's dominant cropping cycles—**Wheat** (Rabi season) and **Rice** (Kharif season)—the application blends machine learning with real-time geospatial environmental data.

By capturing real-time meteorological conditions, soil nutrient metrics, and historical crop performance records, the platform provides district-level yield predictions (quintal/acre), statistical confidence intervals, historical baseline comparisons, and an interactive **What-If Climate Simulator** for stress-testing agricultural outputs against heatwaves or rainfall deficits.

---
---

## ✨ Comprehensive Feature Matrix

1. **🌾 Hyper-Local Crop Modeling:** Specialized regression models tuned specifically for Wheat and Rice production dynamics in Punjab's agro-climatic zones.
2. **📍 Interactive Map & GPS Boundary Lookup:** Real-time spatial indexing using Leaflet map interaction, coordinate pinpointing, or administrative district drop-downs.
3. **🌤️ Zero-Key API Integrations:** Live REST aggregation of weather patterns (Open-Meteo) and topsoil chemical composition (ISRIC SoilGrids).
4. **🔮 "What-If" Sensitivity Simulator:** Real-time perturbation engine allowing farmers to simulate temperature spikes or irrigation deficits to preview predicted yield impacts.
5. **📊 Confidence Scoring & Baselines:** Outputs mathematical reliability scores alongside historical average comparisons.
6. **🇮🇳 Multilingual Accessibility:** Built-in localization support for **English**, **Hindi (हिंदी)**, and **Punjabi (ਪੰਜਾਬੀ)**.

---

## 💻 Prerequisites & Essential Downloads

Ensure all necessary runtimes and developer toolchains are installed before setting up the repository.

### Required Runtimes & Utilities

* 🐍 **Python Runtime (`3.10+`):** [Download Python 3.10+](https://www.python.org/downloads/) — *Essential for running the ML pipeline and FastAPI server.*
* ⚡ **Node.js LTS (`18.x` or `20.x`):** [Download Node.js LTS](https://nodejs.org/en/download) — *Required for building and running the React frontend.*
* 📦 **Git VCS:** [Download Git](https://git-scm.com/downloads) — *Version control system for cloning the repository.*
* 🛠️ **Visual Studio Code:** [Download VS Code](https://code.visualstudio.com/Download) — *Recommended editor.*

### Python Package Dependencies (`backend/requirements.txt`)

Direct download / pip installation list for backend libraries:

* [FastAPI](https://pypi.org/project/fastapi/) (`>=0.100.0`): Modern high-performance web framework.
* [Uvicorn](https://pypi.org/project/uvicorn/) (`>=0.22.0`): Lightning-fast ASGI server implementation.
* [LightGBM](https://pypi.org/project/lightgbm/) (`>=4.0.0`): Gradient boosting framework for ML inference.
* [Scikit-Learn](https://pypi.org/project/scikit-learn/) (`>=1.3.0`): Random Forest models and preprocessing transformers.
* [Pandas](https://pypi.org/project/pandas/) (`>=2.0.0`) & [NumPy](https://pypi.org/project/numpy/) (`>=1.24.0`): Data structures & array computations.
* [GeoPandas](https://pypi.org/project/geopandas/) (`>=0.13.0`) & [Shapely](https://pypi.org/project/shapely/) (`>=2.0.0`): Vector spatial operations.

---

## ⚡ Quick Start & Installation Walkthrough

### Step 1: Clone Repository
```bash
git clone [https://github.com/krishgoyal0023/ai-crop-yield-predictor.git](https://github.com/krishgoyal0023/ai-crop-yield-predictor.git)
cd ai-crop-yield-predictor


Step 2: Configure & Launch Backend Server   
Bash
# Navigate to backend directory
cd backend

# Create virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Create virtual environment (macOS/Linux)
# python3 -m venv venv
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run ML pipeline model training
python model/train.py

# Launch FastAPI development server
uvicorn app:app --reload --port 8000
he API server will start at: http://localhost:8000

Interactive Swagger Documentation: http://localhost:8000/docs


Step 3: Configure & Launch Frontend UI
Open a new terminal window:

Bash
# Navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Start development server
npm run dev
The web app will launch at: http://localhost:5173


🏗️ System Architecture & Workflow Dataflow
The system relies on a decoupled client-server architecture. The frontend collects spatial and crop parameters, which are validated by FastAPI before invoking asynchronous API workers and executing the ensemble ML model.

Complete Data Flow Diagram

-----------------------------------------------------------------------------------+
|                                 REACT FRONTEND UI                                 |
|                       (Leaflet Map / Form / Localization)                         |
+-----------------------------------------------------------------------------------+
                                         │
                                HTTP REST Request (POST)
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                                 FASTAPI BACKEND                                   |
|                                                                                   |
|    ┌─────────────────────────┐         ┌─────────────────────────┐                |
|    │ Open-Meteo Weather API │         │ ISRIC SoilGrids API     │                |
|    └────────────┬────────────┘         └────────────┬────────────┘                |
|                 │                                   │                             |
|                 └─────────────────┬─────────────────┘                             |
|                                   │                                               |
|                                   ▼                                               |
|                     ┌───────────────────────────┐                                 |
|                     │ Feature Vector Processing │                                 |
|                     └─────────────┬─────────────┘                                 |
|                                   │                                               |
|                                   ▼                                               |
|                     ┌───────────────────────────┐                                 |
|                     │ ML Ensemble Inference Engine│                               |
|                     │ LightGBM + Random Forest  │                                 |
|                     └─────────────┬─────────────┘                                 |
+--------------------------------───┼───────────────────────────────────────────────+
                                    │
                         Inference Response (JSON)
                                    │
                                    ▼
+-----------------------------------------------------------------------------------+
|                                 USER DASHBOARD                                    |
|             (Yield Output, Confidence Interval, What-If Simulation)               |
+-----------------------------------------------------------------------------------+


🛠️ API Reference & Specs
Core Endpoints
1. Prediction Endpoint
POST /api/predict

Description: Accepts GPS coordinates, crop selection, and acreage to return yield predictions.

Payload:

JSON
{
  "latitude": 30.9010,
  "longitude": 75.8573,
  "crop": "Wheat",
  "area_acres": 10.0
}
Response:

JSON
{
  "predicted_yield_q_acre": 19.45,
  "total_production_quintals": 194.5,
  "reliability_score_percent": 91.2,
  "district": "Ludhiana",
  "historical_baseline_q_acre": 18.20
}
2. Simulation Endpoint
POST /api/simulate

Description: Computes modified crop yield under custom perturbed weather variables.

📂 Project Directory Map
ai-crop-yield-predictor/
├── backend/
│   ├── app.py                   # FastAPI main entry point & routing
│   ├── requirements.txt         # Backend Python dependencies
│   ├── model/
│   │   ├── __init__.py
│   │   ├── predictor.py         # Model loader & inference execution
│   │   ├── train.py             # Model training pipeline
│   │   └── features.py          # Feature transformation scripts
│   ├── data/
│   │   ├── loader.py            # Historical dataset loaders
│   │   └── cleaner.py           # Preprocessing & cleaning
│   └── utils/
│       ├── weather.py           # Open-Meteo REST API wrapper
│       ├── soil.py              # SoilGrids REST API wrapper
│       └── geo.py               # Spatial lookup utilities
├── frontend/
│   ├── public/                  # Static assets
│   ├── src/
│   │   ├── components/          # Map, Cards, Simulation UI components
│   │   ├── pages/               # Main Application pages
│   │   ├── App.jsx              # React app container
│   │   └── main.jsx             # React entry point
│   ├── package.json             # Frontend NPM configuration
│   ├── tailwind.config.js       # Styling configuration
│   └── vite.config.js           # Vite development server settings
├── data/
│   └── punjab_districts.geojson # GeoJSON boundary layers
├── .gitignore                   # Version control rules
├── LICENSE                      # License file
└── README.md                    # Project documentation
🔗 External Data Sources
Yield Statistics: Data.gov.in DES Punjab Portal

Weather Data Services: Open-Meteo Weather API

Global Soil Layers: ISRIC SoilGrids Database

Satellite Observations: NASA POWER Project

👥 Hackathon Development Team
Member 1 (ML Engineering & Data Pipeline): Model training, hyperparameter tuning, feature engineering.

Member 2 (Geospatial & External APIs): Integration of SoilGrids, Open-Meteo, and GeoJSON boundary filtering.

Member 3 (Frontend Engineering & Localization): React component construction, Leaflet integration, and multi-language UI.

Member 4 (Backend Architecture & Integration): FastAPI routing, Pydantic validation, and deployment pipeline.

📄 License
This repository is distributed under the MIT License. See the LICENSE file for full terms.

Made with ❤️ For IDEAFORGE 2.0 
