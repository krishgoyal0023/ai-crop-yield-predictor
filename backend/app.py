"""
FastAPI main application
Crop Yield Prediction API for Punjab Farmers
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from data.loader import DataLoader
from data.cleaner import DataCleaner
from model.features import FeatureEngineer
from model.predictor import YieldPredictor
from utils.weather import WeatherAPI
from utils.soil import SoilAPI
from utils.geo import find_district_from_coords, is_in_punjab, compute_elevation
from services.intelligence import fertilizer_recommendation, irrigation_schedule, disease_risk, economics, rotation_suggestions, agronomist_answer, ndvi_status
from services.report import build_field_report
from fastapi.responses import StreamingResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Crop Yield Predictor - Punjab",
    description="ML-based crop yield prediction for Wheat and Rice in Punjab, India",
    version="1.0.0"
)

# CORS middleware (allow all origins for hackathon demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
data_loader = DataLoader(data_dir="data")
cleaner = DataCleaner()
weather_api = WeatherAPI()
soil_api = SoilAPI()

# Global variables (loaded at startup)
feature_engineer = None
predictor = None
soil_data = None
models_loaded = False


@app.on_event("startup")
async def startup_event():
    """Load models and data at startup."""
    global feature_engineer, predictor, soil_data, models_loaded

    logger.info("Loading models and data...")

    try:
        # Load data
        yield_df = data_loader.load_yield_data()
        soil_data = data_loader.load_soil_data()

        # Clean
        yield_df, _ = cleaner.clean_pipeline(
            yield_df,
            required_cols=["Year", "District", "Crop", "Season", "Area", "Yield"]
        )

        # Engineer features
        feature_engineer = FeatureEngineer()
        feature_df = feature_engineer.engineer_features(yield_df, soil_data, is_training=True)

        # Load predictor
        predictor = YieldPredictor(model_dir="models")
        predictor._save_baselines(feature_df)

        models_loaded = True
        logger.info("Models and data loaded successfully!")

    except Exception as e:
        logger.error(f"Error loading models: {e}")
        models_loaded = False


# ============== REQUEST/RESPONSE MODELS ==============

class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=29.0, le=33.0, description="Latitude (Punjab bounds)")
    longitude: float = Field(..., ge=73.0, le=77.0, description="Longitude (Punjab bounds)")


class PredictRequest(BaseModel):
    latitude: float = Field(..., description="Field latitude")
    longitude: float = Field(..., description="Field longitude")
    crop: str = Field(..., description="Crop name: Wheat or Rice")
    seed_variety: Optional[str] = Field(None, description="Seed variety (optional)")
    sowing_date: Optional[str] = Field(None, description="Sowing date (YYYY-MM-DD)")
    farm_area: float = Field(1.0, description="Farm area in hectares")
    stage: str = Field("sowing", description="Prediction stage: sowing, midseason, preharvest")
    irrigation: Optional[str] = Field(None, description="Irrigation type (optional)")
    previous_crop: Optional[str] = Field(None, description="Previous crop (optional)")
    soil_test_ph: Optional[float] = Field(None, description="Soil pH from lab test (optional)")
    soil_test_n: Optional[float] = Field(None, description="Soil nitrogen (optional)")
    override_weather: Optional[Dict] = Field(None, description="Override weather data (advanced)")


class SimulateRequest(BaseModel):
    latitude: float
    longitude: float
    crop: str
    scenarios: List[Dict] = Field(..., description="List of scenario parameters to simulate")


# ============== API ENDPOINTS ==============

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "AI Crop Yield Predictor - Punjab API",
        "version": "1.0.0",
        "models_loaded": models_loaded,
        "crops_supported": ["Wheat", "Rice"],
        "region": "Punjab, India"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy" if models_loaded else "degraded",
        "models_loaded": models_loaded,
        "data_available": soil_data is not None
    }


@app.post("/location")
async def get_location_info(request: LocationRequest):
    """
    Get location information from coordinates.

    Returns district, state, region, elevation, and validity check.
    """
    lat, lon = request.latitude, request.longitude

    # Validate within Punjab
    if not is_in_punjab(lat, lon):
        raise HTTPException(
            status_code=400,
            detail=f"Coordinates ({lat}, {lon}) are outside Punjab state bounds"
        )

    # Find district
    district = find_district_from_coords(lat, lon)

    # Get elevation
    elevation = compute_elevation(lat, lon)

    return {
        "latitude": lat,
        "longitude": lon,
        "district": district,
        "state": "Punjab",
        "country": "India",
        "region": "Punjab Plains",
        "elevation_m": round(elevation, 1),
        "valid": district is not None,
        "message": "Location identified" if district else "Location outside Punjab districts"
    }


@app.get("/weather/{lat}/{lon}")
async def get_weather(lat: float, lon: float, season: str = "Rabi"):
    """
    Get weather data for a location.

    Falls back to Punjab climatology if API fails.
    """
    if not is_in_punjab(lat, lon):
        raise HTTPException(status_code=400, detail="Coordinates outside Punjab")

    # Try Open-Meteo historical
    import datetime
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)

    weather_df = weather_api.get_openmeteo_historical(
        lat, lon,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
        season
    )

    if weather_df is not None:
        features = weather_api.compute_seasonal_features(weather_df, season, end_date.year)
        return {
            "source": "Open-Meteo",
            "location": {"lat": lat, "lon": lon},
            "season": season,
            "features": features
        }
    else:
        # Fallback to climatology
        features = weather_api._get_punjab_climatology(season)
        return {
            "source": "Punjab climatology (fallback)",
            "location": {"lat": lat, "lon": lon},
            "season": season,
            "features": features,
            "note": "Using historical averages for Punjab"
        }


@app.get("/soil/{lat}/{lon}")
async def get_soil(lat: float, lon: float):
    """
    Get soil data for a location.

    Tries SoilGrids API, falls back to district averages.
    """
    if not is_in_punjab(lat, lon):
        raise HTTPException(status_code=400, detail="Coordinates outside Punjab")

    # Try SoilGrids
    soil = soil_api.get_soil_properties(lat, lon)

    if soil is None:
        # Fallback to district-level
        district = find_district_from_coords(lat, lon)
        if district:
            soil = soil_api.get_district_soil_fallback(district)
            source = "District average (Punjab)"
        else:
            # Punjab average
            soil = soil_api.get_district_soil_fallback("Ludhiana")
            source = "Punjab state average"
    else:
        source = "SoilGrids (ISRIC)"

    # Add soil type classification
    if "Clay" in soil and "Sand" in soil and "Silt" in soil:
        soil["Soil_Type"] = soil_api.classify_soil_type(
            soil["Clay"], soil["Sand"], soil["Silt"]
        )

    return {
        "source": source,
        "location": {"lat": lat, "lon": lon},
        "properties": soil,
        "method": "estimated"  # SoilGrids is modeled, not measured
    }


@app.post("/predict")
async def predict_yield(request: PredictRequest):
    """
    Predict crop yield for a field.

    Returns prediction with confidence interval, reliability, and explanation.
    """
    if not models_loaded:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Please run train_model.py first."
        )

    # Validate location
    if not is_in_punjab(request.latitude, request.longitude):
        raise HTTPException(
            status_code=400,
            detail="Location must be within Punjab, India"
        )

    # Validate crop
    if request.crop not in ["Wheat", "Rice"]:
        raise HTTPException(
            status_code=400,
            detail="Crop must be 'Wheat' or 'Rice'"
        )

    # Determine district
    district = find_district_from_coords(request.latitude, request.longitude)
    if not district:
        district = "Ludhiana"  # Fallback

    # Determine season from crop
    season = "Rabi" if request.crop == "Wheat" else "Kharif"

    # Get current year
    import datetime
    year = datetime.date.today().year

    # Auto-derive data
    data_completeness = 1.0
    data_sources = {
        "soil": "SoilGrids (estimated)",
        "weather": "Open-Meteo (historical)",
        "satellite": "Not available (MVP)",
        "geographic": f"District: {district}",
        "osm": "Not used (MVP)"
    }

    # Try to fetch weather
    weather_features = {}
    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=365)
        weather_df = weather_api.get_openmeteo_historical(
            request.latitude, request.longitude,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            season
        )
        if weather_df is not None:
            weather_features = weather_api.compute_seasonal_features(weather_df, season, year)
            data_sources["weather"] = "Open-Meteo"
        else:
            weather_features = weather_api._get_punjab_climatology(season)
            data_completeness -= 0.2
            data_sources["weather"] = "Punjab climatology (fallback)"
    except Exception as e:
        logger.warning(f"Weather fetch failed: {e}")
        weather_features = weather_api._get_punjab_climatology(season)
        data_completeness -= 0.2

    # Try to fetch soil
    soil_features = {}
    try:
        soil_features = soil_api.get_soil_properties(request.latitude, request.longitude)
        if soil_features is None:
            soil_features = soil_api.get_district_soil_fallback(district)
            data_sources["soil"] = "District average (fallback)"
            data_completeness -= 0.15
        else:
            data_sources["soil"] = "SoilGrids (estimated)"
    except Exception as e:
        logger.warning(f"Soil fetch failed: {e}")
        soil_features = soil_api.get_district_soil_fallback(district)
        data_completeness -= 0.15

    # Build feature row
    farmer_input = {
        "year": year,
        "district": district,
        "crop": request.crop,
        "season": season,
        "area": request.farm_area,
        "seed": request.seed_variety or "Not specified",
        "stage": request.stage,
    }

    # Create feature DataFrame
    import pandas as pd
    features_df = pd.DataFrame([{
        "Year": year,
        "District": district,
        "Crop": request.crop,
        "Season": season,
        "Area": request.farm_area,
    }])

    # Engineer features
    if feature_engineer:
        # Add weather features
        for key, value in weather_features.items():
            features_df[key] = value

        # Add soil features
        for key, value in soil_features.items():
            features_df[key] = value

        # Add geographic features
        features_df["Latitude"] = request.latitude
        features_df["Longitude"] = request.longitude

        # Add historical features (will use lagged values)
        features_df = feature_engineer._add_basic_features(features_df)
        features_df = feature_engineer._add_historical_features(features_df, is_training=False)
        features_df = feature_engineer._add_geographic_features(features_df)
        features_df = feature_engineer._encode_categoricals(features_df, is_training=False)

    # Make prediction
    try:
        result = predictor.predict(
            features=features_df,
            district=district,
            crop=request.crop,
            data_completeness=data_completeness,
            data_sources=data_sources
        )

        return {
            "field_location": {"latitude": request.latitude, "longitude": request.longitude},
            "district": result.district,
            "crop": result.crop,
            "seed": result.seed,
            "stage": result.stage,
            "predicted_yield": result.predicted_yield,
            "unit": result.unit,
            "prediction_interval": result.prediction_interval,
            "historical_baseline": result.historical_baseline,
            "deviation_from_baseline": result.deviation_from_baseline,
            "reliability": result.reliability,
            "reliability_reasons": result.reliability_reasons,
            "data_completeness": result.data_completeness,
            "data_sources": result.data_sources,
            "important_features": result.important_features,
            "explanation": result.explanation,
            "disclaimer": "This is a model simulation based on historical patterns. Actual yields may vary."
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/simulate")
async def simulate_what_if(request: SimulateRequest):
    """
    What-if simulation: predict yield under different scenarios.

    Example scenarios:
    - Change irrigation type
    - Change sowing date
    - Add fertilizer
    """
    if not models_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")

    results = []

    for scenario in request.scenarios:
        # Modify request with scenario parameters
        sim_request = PredictRequest(
            latitude=request.latitude,
            longitude=request.longitude,
            crop=request.crop,
            **scenario
        )

        try:
            result = await predict_yield(sim_request)
            results.append({
                "scenario": scenario,
                "prediction": result
            })
        except Exception as e:
            results.append({
                "scenario": scenario,
                "error": str(e)
            })

    return {
        "crop": request.crop,
        "location": {"lat": request.latitude, "lon": request.longitude},
        "scenarios": results,
        "note": "These are model simulations, not guaranteed outcomes"
    }


@app.get("/crop-information/{crop}")
async def get_crop_info(crop: str):
    """
    Get information about a crop (Wheat or Rice).

    Returns agronomic information, optimal conditions, etc.
    """
    crop = crop.capitalize()

    crop_info = {
        "Wheat": {
            "name": "Wheat (गेहूं)",
            "name_punjabi": "ਗੇਹੂੰ",
            "season": "Rabi (Winter)",
            "sowing_months": "October - November",
            "harvest_months": "March - April",
            "optimal_ph": "6.0 - 7.5",
            "optimal_temperature": "15-25°C",
            "water_requirement": "450-650 mm",
            "major_varieties_punjab": ["PBW-550", "PBW-343", "HD-2967", "DBW-17"],
            "average_yield_punjab": "4.5 - 5.5 tonnes/ha",
            "description": "Wheat is the main rabi crop in Punjab, sown after rice harvesting."
        },
        "Rice": {
            "name": "Rice (चावल / ਪੁੱਸ਼ਤ)",
            "name_punjabi": "ਚਾਵਲ",
            "season": "Kharif (Monsoon)",
            "sowing_months": "June - July",
            "harvest_months": "October - November",
            "optimal_ph": "5.5 - 6.5",
            "optimal_temperature": "20-35°C",
            "water_requirement": "1200-1500 mm",
            "major_varieties_punjab": ["PR-121", "PR-126", "PUSA-44", "PAU-201"],
            "average_yield_punjab": "3.8 - 4.5 tonnes/ha",
            "description": "Rice is the main kharif crop in Punjab, cultivated during monsoon season."
        }
    }

    if crop not in crop_info:
        raise HTTPException(status_code=404, detail="Crop not found. Supported: Wheat, Rice")

    return crop_info[crop]


@app.get("/districts")
async def get_districts():
    """Get list of supported districts in Punjab."""
    from utils.geo import PUNJAB_DISTRICTS

    districts = []
    for name, info in PUNJAB_DISTRICTS.items():
        districts.append({
            "name": name,
            "region": info["region"],
            "coordinates": {"lat": info["lat"], "lon": info["lon"]}
        })

    return {
        "state": "Punjab",
        "total_districts": len(districts),
        "districts": districts
    }


@app.get("/model-info")
async def get_model_info():
    """Get information about the trained model."""
    if not models_loaded:
        return {"status": "not_loaded"}

    return {
        "status": "loaded",
        "model_type": "LightGBM",
        "crops": ["Wheat", "Rice"],
        "features_used": len(predictor.feature_names) if predictor else 0,
        "feature_list": predictor.feature_names if predictor else [],
        "baselines_loaded": len(predictor.baselines) if predictor else 0,
        "data_period": "2010-2023",
        "validation": "Temporal split (train: 2010-2020, val: 2021-2022, test: 2023)"
    }


# ============== FARM INTELLIGENCE ==============

class FertilizerRequest(BaseModel):
    crop: str
    soil: Dict = {}
    area_ha: float = Field(1.0, gt=0)
    target_yield_t_ha: Optional[float] = None
    previous_crop: Optional[str] = None
    lcc: Optional[float] = None

class IrrigationRequest(BaseModel):
    latitude: float
    longitude: float
    crop: str
    stage: str = "midseason"
    area_ha: float = Field(1.0, gt=0)
    efficiency: float = Field(0.75, gt=0.1, le=1.0)
    pump_lpm: Optional[float] = Field(None, gt=0)

class DiseaseRequest(BaseModel):
    crop: str
    latitude: float
    longitude: float
    stage: str = "midseason"

class EconomicsRequest(BaseModel):
    crop: str
    predicted_yield_t_ha: float = Field(..., ge=0)
    area_ha: float = Field(1.0, gt=0)
    sale_price_per_quintal: Optional[float] = Field(None, gt=0)
    costs_per_ha: Dict[str, float] = {}

class RotationRequest(BaseModel):
    crop: str
    water_available: str = "normal"

class AgronomistRequest(BaseModel):
    question: str = Field(..., min_length=2)
    crop: str = "Wheat"
    stage: str = "midseason"
    soil: Dict = {}
    weather: Dict = {}

@app.post("/fertilizer/recommend")
async def recommend_fertilizer(request: FertilizerRequest):
    try:
        return fertilizer_recommendation(request.crop, request.soil, request.area_ha, request.target_yield_t_ha, request.previous_crop, request.lcc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/irrigation/schedule")
async def get_irrigation_schedule(request: IrrigationRequest):
    if not is_in_punjab(request.latitude, request.longitude):
        raise HTTPException(status_code=400, detail="Coordinates outside Punjab")
    try:
        return irrigation_schedule(request.latitude, request.longitude, request.crop, request.stage, request.area_ha, request.efficiency, request.pump_lpm)
    except Exception as e:
        logger.exception("Irrigation service failed")
        raise HTTPException(status_code=502, detail=f"Irrigation weather service failed: {e}")

@app.post("/disease/risk")
async def get_disease_risk(request: DiseaseRequest):
    if not is_in_punjab(request.latitude, request.longitude):
        raise HTTPException(status_code=400, detail="Coordinates outside Punjab")
    try:
        forecast = irrigation_schedule(request.latitude, request.longitude, request.crop, request.stage, 1.0, 0.75, None)
        return disease_risk(request.crop, forecast, request.stage)
    except Exception as e:
        logger.exception("Disease service failed")
        raise HTTPException(status_code=502, detail=f"Disease weather service failed: {e}")

@app.post("/economics/calculate")
async def calculate_economics(request: EconomicsRequest):
    return economics(request.crop, request.predicted_yield_t_ha, request.area_ha, request.sale_price_per_quintal, request.costs_per_ha)

@app.post("/rotation/suggestions")
async def get_rotation_suggestions(request: RotationRequest):
    return rotation_suggestions(request.crop, request.water_available)

@app.post("/agronomist")
async def ask_agronomist(request: AgronomistRequest):
    return agronomist_answer(request.question, request.crop, request.stage, request.soil, request.weather)

@app.get("/ndvi/status")
async def get_ndvi_status():
    return ndvi_status()

@app.get("/health/services")
async def service_health():
    return {"ml_model": models_loaded, "weather": "Open-Meteo configured", "soil": "SoilGrids + district fallback configured", "irrigation": "Open-Meteo ET0 configured", "disease": "Weather-rule engine configured", "economics": "MSP 2026-27 dataset configured", "ndvi": "Credentials required for live Sentinel-2 processing"}


class ReportRequest(BaseModel):
    location: Dict = {}
    district: Optional[str] = None
    crop: Optional[str] = None
    area_ha: Optional[float] = None
    prediction: Dict = {}
    fertilizer: Dict = {}
    irrigation: Dict = {}
    disease: Dict = {}
    economics: Dict = {}
    rotation: Dict = {}

@app.post("/report")
async def create_report(request: ReportRequest):
    pdf=build_field_report(request.model_dump())
    return StreamingResponse(pdf, media_type="application/pdf", headers={"Content-Disposition":"attachment; filename=field-assessment.pdf"})


# Run with: uvicorn app:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
