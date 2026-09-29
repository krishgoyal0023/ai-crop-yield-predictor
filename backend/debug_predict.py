import sys, traceback
sys.path.insert(0, "C:/Users/DELL/ai crop predictor")
try:
    from backend.model.predictor import YieldPredictor
    from backend.model.features import FeatureEngineer
    import pandas as pd

    predictor = YieldPredictor(model_dir="C:/Users/DELL/ai crop predictor/backend/models")
    engineer = FeatureEngineer()

    row = {
        "Year": 2024, "District": "Ludhiana", "Crop": "Wheat", "Season": "Rabi", "Area": 1.0,
        "rainfall_total": 150.0, "temp_avg": 20.0, "gdd": 1200.0, "heat_stress_days": 3.0,
        "pH": 7.5, "SOC": 0.7, "N": 170.0, "P": 16.0, "K": 230.0,
        "Clay": 24.0, "Soil_Quality": 0.8, "Latitude": 30.9, "Longitude": 75.5,
    }
    df = pd.DataFrame([row])
    df = engineer._add_basic_features(df)
    df = engineer._add_historical_features(df, is_training=False)
    df = engineer._add_geographic_features(df)
    df = engineer._add_soil_features(df, None)
    df = engineer._encode_categoricals(df, is_training=False)
    print("cols:", df.columns.tolist())
    print("missing model cols:", [c for c in predictor.feature_names if c not in df.columns])

    r = predictor.predict(features=df, district="Ludhiana", crop="Wheat", data_completeness=1.0)
    print("OK:", r.predicted_yield)
except Exception:
    traceback.print_exc()
