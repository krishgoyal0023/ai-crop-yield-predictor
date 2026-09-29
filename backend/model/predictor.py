"""
ML Model predictor wrapper
Handles inference, uncertainty estimation, and explainability
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Structured prediction output."""
    field_location: Dict[str, float]
    district: str
    crop: str
    seed: str
    stage: str
    predicted_yield: float
    unit: str
    prediction_interval: Dict[str, float]
    historical_baseline: float
    deviation_from_baseline: float
    reliability: str
    reliability_reasons: List[str]
    data_completeness: float
    data_sources: Dict[str, str]
    important_features: List[Dict[str, float]]
    explanation: str


class YieldPredictor:
    """Wrapper for yield prediction model."""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model = None
        self.feature_names = []
        self.feature_stats = {}
        self.baselines = {}  # District-crop baselines
        self._load_model()
        self._load_baselines()

    def _load_model(self):
        """Load trained model from disk."""
        model_path = self.model_dir / "lightgbm_model.pkl"
        feature_path = self.model_dir / "lightgbm_model_features.json"

        if model_path.exists():
            self.model = joblib.load(model_path)
            logger.info("Loaded LightGBM model")

        if feature_path.exists():
            with open(feature_path, "r") as f:
                self.feature_names = json.load(f)
            logger.info(f"Loaded {len(self.feature_names)} feature names")

    def _load_baselines(self):
        """Load historical baselines for reliability scoring."""
        baseline_path = self.model_dir / "baselines.json"
        if baseline_path.exists():
            with open(baseline_path, "r") as f:
                self.baselines = json.load(f)

    def _save_baselines(self, df: pd.DataFrame):
        """Compute and save district-crop baselines."""
        baselines = {}
        for (district, crop), group in df.groupby(["District", "Crop"]):
            recent = group[group["Year"] >= 2018]
            if len(recent) > 0:
                baselines[f"{district}_{crop}"] = {
                    "mean": float(recent["Yield"].mean()),
                    "std": float(recent["Yield"].std()),
                    "years": int(len(recent))
                }

        self.baselines = baselines
        baseline_path = self.model_dir / "baselines.json"
        with open(baseline_path, "w") as f:
            json.dump(baselines, f, indent=2)

    def predict(
        self,
        features: pd.DataFrame,
        district: str,
        crop: str,
        data_completeness: float = 1.0,
        data_sources: Dict[str, str] = None
    ) -> PredictionResult:
        """
        Make a yield prediction.

        Args:
            features: Engineered feature DataFrame (single row)
            district: District name
            crop: Crop name (Wheat/Rice)
            data_completeness: Fraction of features available (0-1)
            data_sources: Dictionary of data source provenance

        Returns:
            PredictionResult with prediction, intervals, and explanation
        """
        if self.model is None:
            return self._fallback_prediction(district, crop)

        # Prepare features
        X = self._prepare_features(features)

        # Predict
        y_pred = self.model.predict(X)[0]

        # Uncertainty estimate (prediction interval)
        # Use model's prediction std from training residuals
        pred_interval = self._estimate_interval(y_pred, district, crop)

        # Historical baseline
        baseline_key = f"{district}_{crop}"
        baseline = self.baselines.get(baseline_key, {}).get("mean", y_pred)
        deviation = y_pred - baseline

        # Reliability assessment
        reliability, reasons = self._assess_reliability(
            data_completeness, district, crop, features
        )

        # Feature importance
        important_features = self._get_top_features(features)

        # Explanation
        explanation = self._generate_explanation(
            y_pred, baseline, deviation, important_features, crop
        )

        # Data sources
        if data_sources is None:
            data_sources = {
                "soil": "SoilGrids (estimated)",
                "weather": "Open-Meteo climatology",
                "satellite": "Not available",
                "geographic": "District centroid",
                "osm": "Not used"
            }

        return PredictionResult(
            field_location={
                "latitude": features.get("Latitude", [30.5])[0] if "Latitude" in features else 30.5,
                "longitude": features.get("Longitude", [75.5])[0] if "Longitude" in features else 75.5,
            },
            district=district,
            crop=crop,
            seed=features.get("seed", ["Not specified"])[0] if "seed" in features else "Not specified",
            stage=features.get("stage", ["Sowing"])[0] if "stage" in features else "Sowing",
            predicted_yield=round(y_pred / 1000, 2),  # Convert kg/ha to tonnes/ha
            unit="tonnes_per_hectare",
            prediction_interval={
                "lower": round(pred_interval[0] / 1000, 2),  # kg/ha → t/ha
                "upper": round(pred_interval[1] / 1000, 2),
                "method": "historical_mae"
            },
            historical_baseline=round(baseline / 1000, 2),  # Convert kg to tonnes
            deviation_from_baseline=round(deviation / 1000, 2),
            reliability=reliability,
            reliability_reasons=reasons,
            data_completeness=round(data_completeness, 2),
            data_sources=data_sources,
            important_features=important_features[:5],
            explanation=explanation
        )

    def _prepare_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Ensure features match model expectations."""
        # Add missing features with defaults
        for feat in self.feature_names:
            if feat not in features.columns:
                features[feat] = 0.0

        # Select only model features
        X = features[self.feature_names].fillna(0)
        return X

    def _estimate_interval(self, y_pred: float, district: str, crop: str) -> Tuple[float, float]:
        """
        Estimate prediction interval.

        Uses historical MAE as uncertainty estimate.
        """
        # MAE from validation: typically 300-500 kg/ha
        mae = 400  # kg/ha, calibrated on validation set

        # Adjust for data completeness
        baseline_key = f"{district}_{crop}"
        baseline_info = self.baselines.get(baseline_key, {})
        if baseline_info.get("years", 0) < 3:
            mae *= 1.5  # Wider interval for data-sparse districts

        lower = max(0, y_pred - mae)
        upper = y_pred + mae

        return (lower, upper)

    def _assess_reliability(
        self,
        data_completeness: float,
        district: str,
        crop: str,
        features: pd.DataFrame
    ) -> Tuple[str, List[str]]:
        """
        Assess prediction reliability.

        Returns:
            Tuple of (reliability_level, list_of_reasons)
        """
        reasons = []

        # Check data completeness
        if data_completeness < 0.5:
            reasons.append("Limited automatic data available; predictions are less reliable")
            reliability = "Low"
        elif data_completeness < 0.8:
            reasons.append("Some data sources unavailable; moderate reliability")
            reliability = "Medium"
        else:
            reliability = "High"

        # Check if district has sufficient training data
        baseline_key = f"{district}_{crop}"
        baseline_info = self.baselines.get(baseline_key, {})
        if baseline_info.get("years", 0) < 5:
            reasons.append(f"Only {baseline_info.get('years', 0)} years of data for {district} {crop}")
            if reliability == "High":
                reliability = "Medium"
            else:
                reliability = "Low"

        # Check for unusual conditions
        if "rainfall_total" in features.columns:
            rainfall = features["rainfall_total"].iloc[0]
            if crop == "Wheat" and rainfall > 500:
                reasons.append("Unusually high rainfall for wheat season")
            elif crop == "Rice" and rainfall < 200:
                reasons.append("Unusually low rainfall for rice season")

        if not reasons:
            reasons.append("Sufficient data and normal conditions")

        return reliability, reasons

    def _get_top_features(self, features: pd.DataFrame) -> List[Dict]:
        """Get top contributing features for explanation."""
        if self.model is None or not hasattr(self.model, "feature_importances_"):
            return []

        importance = self.model.feature_importances_
        feature_importance = list(zip(self.feature_names, importance))
        feature_importance.sort(key=lambda x: x[1], reverse=True)

        top_features = []
        for name, imp in feature_importance[:5]:
            if name in features.columns:
                val = features[name].iloc[0]
                top_features.append({
                    "feature": name,
                    "importance": round(float(imp), 4),
                    "value": round(float(val), 2)
                })

        return top_features

    def _generate_explanation(
        self,
        y_pred: float,
        baseline: float,
        deviation: float,
        important_features: List[Dict],
        crop: str
    ) -> str:
        """Generate farmer-friendly explanation."""
        y_pred_tonnes = y_pred / 1000
        baseline_tonnes = baseline / 1000

        if deviation > 200:
            direction = "above"
            comparison = "better than"
        elif deviation < -200:
            direction = "below"
            comparison = "lower than"
        else:
            direction = "near"
            comparison = "similar to"

        explanation = (
            f"The model predicts a yield of {y_pred_tonnes:.2f} tonnes per hectare for {crop}, "
            f"which is {direction} the district average of {baseline_tonnes:.2f} tonnes per hectare. "
            f"This prediction is {comparison} the typical yield for your area. "
            f"Key factors influencing this prediction include: "
            f"{', '.join([f['feature'] for f in important_features[:3]])}. "
            f"This is a model simulation and actual yields may vary based on farming practices, "
            f"weather conditions during the season, and other factors."
        )

        return explanation

    def _fallback_prediction(self, district: str, crop: str) -> PredictionResult:
        """Fallback when model is not loaded."""
        # Use district average as fallback
        baseline_key = f"{district}_{crop}"
        baseline = self.baselines.get(baseline_key, {}).get("mean", 4000)

        return PredictionResult(
            field_location={"latitude": 30.5, "longitude": 75.5},
            district=district,
            crop=crop,
            seed="Not specified",
            stage="Sowing",
            predicted_yield=round(baseline / 1000, 2),
            unit="tonnes_per_hectare",
            prediction_interval={
                "lower": round((baseline - 500) / 1000, 2),
                "upper": round((baseline + 500) / 1000, 2),
                "method": "historical_mean"
            },
            historical_baseline=round(baseline / 1000, 2),
            deviation_from_baseline=0.0,
            reliability="Medium",
            reliability_reasons=["Using historical average; model not loaded"],
            data_completeness=0.5,
            data_sources={"soil": "Default", "weather": "Default", "satellite": "N/A", "geographic": "Default"},
            important_features=[],
            explanation="Using district average yield as model is not loaded."
        )
