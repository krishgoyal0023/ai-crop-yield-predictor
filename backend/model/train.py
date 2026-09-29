"""
Model training pipeline
Implements ablation ladder: Model 0 (mean) → 1 (history) → 2 (+weather) → 3 (+soil) → 4 (+geo)
Trains LightGBM, RandomForest, XGBoost, and Linear models
Validates with temporal split (no random splits)
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import logging

from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)

# Try to import LightGBM and XGBoost
try:
    from lightgbm import LGBMRegressor
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    logger.warning("LightGBM not available")

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("XGBoost not available")


class ModelTrainer:
    """Train and evaluate crop yield prediction models."""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.models = {}
        self.results = {}

    def train_ablation_ladder(
        self,
        df: pd.DataFrame,
        feature_engineer
    ) -> Dict:
        """
        Train models with increasing feature sets (ablation study).

        Args:
            df: Full feature DataFrame
            feature_engineer: FeatureEngineer instance

        Returns:
            Dictionary with all model results
        """
        results = {}

        # Define feature sets (ablation ladder)
        feature_sets = {
            "Model0_Mean": [],  # Just predict mean
            "Model1_History": ["Crop_Code", "Season_Code", "log_Area", "Yield_Lag1", "Yield_MA3", "Yield_MA5", "District_Encoded"],
            "Model2_Weather": ["Crop_Code", "Season_Code", "log_Area", "Yield_Lag1", "Yield_MA3", "Yield_MA5",
                               "District_Encoded", "rainfall_total", "temp_avg", "gdd", "heat_stress_days"],
            "Model3_Soil": ["Crop_Code", "Season_Code", "log_Area", "Yield_Lag1", "Yield_MA3", "Yield_MA5",
                            "District_Encoded", "rainfall_total", "temp_avg", "gdd",
                            "pH", "SOC", "N", "P", "K", "Clay", "Soil_Quality"],
            "Model4_Full": feature_engineer.get_feature_list(df),
        }

        target = "Yield"

        for model_name, features in feature_sets.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Training {model_name} with {len(features)} features")
            logger.info(f"Features: {features}")

            # Filter to available features
            available_features = [f for f in features if f in df.columns]
            if len(available_features) < 2:
                logger.warning(f"Skipping {model_name}: insufficient features")
                continue

            # Split: temporal (train on 2010-2020, val on 2021-2022, test on 2023)
            train_mask = df["Year"] <= 2020
            val_mask = (df["Year"] >= 2021) & (df["Year"] <= 2022)
            test_mask = df["Year"] >= 2023

            X_train = df.loc[train_mask, available_features].fillna(0)
            y_train = df.loc[train_mask, target]

            X_val = df.loc[val_mask, available_features].fillna(0)
            y_val = df.loc[val_mask, target]

            X_test = df.loc[test_mask, available_features].fillna(0)
            y_test = df.loc[test_mask, target]

            if len(X_test) == 0:
                # If no 2023 data, use 2022 as test
                test_mask = df["Year"] == df["Year"].max()
                X_test = df.loc[test_mask, available_features].fillna(0)
                y_test = df.loc[test_mask, target]

            logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

            # Train multiple algorithms
            model_results = self._train_multiple_models(
                X_train, y_train, X_val, y_val, X_test, y_test, model_name
            )

            results[model_name] = {
                "features": available_features,
                "num_features": len(available_features),
                "models": model_results,
                "best_model": max(model_results, key=lambda m: model_results[m].get("test_r2", -999))
            }

        self.results = results
        return results

    def _train_multiple_models(
        self,
        X_train, y_train,
        X_val, y_val,
        X_test, y_test,
        model_name: str
    ) -> Dict:
        """Train multiple model types and return metrics."""

        results = {}

        # Model 0: Mean baseline
        if model_name == "Model0_Mean":
            mean_pred = np.full(len(y_test), y_train.mean())
            results["Mean"] = self._compute_metrics(y_test, mean_pred, "Mean")
            return results

        # 1. Linear Regression (Ridge)
        try:
            ridge = Ridge(alpha=1.0, random_state=42)
            ridge.fit(X_train, y_train)
            y_pred = ridge.predict(X_test)
            results["Ridge"] = self._compute_metrics(y_test, y_pred, "Ridge")
            logger.info(f"  Ridge: R²={results['Ridge']['test_r2']:.4f}, MAE={results['Ridge']['test_mae']:.2f}")
        except Exception as e:
            logger.error(f"Ridge training failed: {e}")

        # 2. Random Forest
        try:
            rf = RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            rf.fit(X_train, y_train)
            y_pred = rf.predict(X_test)
            results["RandomForest"] = self._compute_metrics(y_test, y_pred, "RandomForest")
            logger.info(f"  RF: R²={results['RandomForest']['test_r2']:.4f}, MAE={results['RandomForest']['test_mae']:.2f}")
        except Exception as e:
            logger.error(f"RandomForest training failed: {e}")

        # 3. Gradient Boosting (sklearn)
        try:
            gb = GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                min_samples_split=5,
                random_state=42
            )
            gb.fit(X_train, y_train)
            y_pred = gb.predict(X_test)
            results["GradientBoosting"] = self._compute_metrics(y_test, y_pred, "GradientBoosting")
            logger.info(f"  GB: R²={results['GradientBoosting']['test_r2']:.4f}, MAE={results['GradientBoosting']['test_mae']:.2f}")
        except Exception as e:
            logger.error(f"GradientBoosting training failed: {e}")

        # 4. LightGBM
        if HAS_LIGHTGBM:
            try:
                lgbm = LGBMRegressor(
                    n_estimators=300,
                    max_depth=8,
                    learning_rate=0.05,
                    num_leaves=31,
                    min_child_samples=10,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbose=-1
                )
                lgbm.fit(X_train, y_train, eval_set=[(X_val, y_val)], callbacks=[])
                y_pred = lgbm.predict(X_test)
                results["LightGBM"] = self._compute_metrics(y_test, y_pred, "LightGBM")
                logger.info(f"  LGBM: R²={results['LightGBM']['test_r2']:.4f}, MAE={results['LightGBM']['test_mae']:.2f}")

                # Store LightGBM model for later
                if model_name == "Model4_Full":
                    self.models["lightgbm"] = lgbm
                    self._save_model(lgbm, "lightgbm_model.pkl", list(X_train.columns))

            except Exception as e:
                logger.error(f"LightGBM training failed: {e}")

        # 5. XGBoost
        if HAS_XGBOOST:
            try:
                xgb = XGBRegressor(
                    n_estimators=300,
                    max_depth=6,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbosity=0
                )
                xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
                y_pred = xgb.predict(X_test)
                results["XGBoost"] = self._compute_metrics(y_test, y_pred, "XGBoost")
                logger.info(f"  XGB: R²={results['XGBoost']['test_r2']:.4f}, MAE={results['XGBoost']['test_mae']:.2f}")
            except Exception as e:
                logger.error(f"XGBoost training failed: {e}")

        return results

    def _compute_metrics(self, y_true, y_pred, model_name: str) -> Dict:
        """Compute regression metrics."""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)

        # MAPE (only if no zero values)
        if np.all(y_true > 0):
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        else:
            mape = None

        # Prediction interval (simple: ±MAE)
        pred_lower = y_pred - mae
        pred_upper = y_pred + mae

        return {
            "model": model_name,
            "test_mae": round(mae, 2),
            "test_rmse": round(rmse, 2),
            "test_r2": round(r2, 4),
            "test_mape": round(mape, 2) if mape else None,
            "prediction_interval_width": round(mae * 2, 2),
            "predictions": y_pred.tolist()[:10],  # Store first 10 for inspection
        }

    def _save_model(self, model, filename: str, feature_names: List[str]):
        """Save model to disk."""
        filepath = self.model_dir / filename
        joblib.dump(model, filepath)

        # Save feature names
        feature_file = self.model_dir / f"{filename.replace('.pkl', '_features.json')}"
        with open(feature_file, "w") as f:
            json.dump(feature_names, f, indent=2)

        logger.info(f"Saved model to {filepath}")

    def load_model(self, filename: str = "lightgbm_model.pkl"):
        """Load trained model."""
        filepath = self.model_dir / filename
        if filepath.exists():
            model = joblib.load(filepath)

            # Load feature names
            feature_file = self.model_dir / f"{filename.replace('.pkl', '_features.json')}"
            if feature_file.exists():
                with open(feature_file, "r") as f:
                    features = json.load(f)
                return model, features

            return model, []
        return None, []

    def train_per_crop_models(self, df: pd.DataFrame, feature_engineer) -> Dict:
        """
        Train separate models for Wheat and Rice.
        Compare with single global model.
        """
        results = {}

        for crop in ["Wheat", "Rice"]:
            crop_df = df[df["Crop"] == crop].copy()
            logger.info(f"\nTraining {crop}-specific model with {len(crop_df)} records")

            if len(crop_df) < 20:
                logger.warning(f"Insufficient data for {crop}")
                continue

            # Get feature list
            features = feature_engineer.get_feature_list(crop_df)
            available = [f for f in features if f in crop_df.columns]
            available = [f for f in available if crop_df[f].notna().sum() > len(crop_df) * 0.5]

            if len(available) < 3:
                continue

            X = crop_df[available].fillna(0)
            y = crop_df["Yield"]

            # Temporal split
            train_mask = crop_df["Year"] <= 2020
            test_mask = crop_df["Year"] >= 2021

            X_train, X_test = X[train_mask], X[test_mask]
            y_train, y_test = y[train_mask], y[test_mask]

            if len(X_test) == 0:
                continue

            # Train LightGBM
            if HAS_LIGHTGBM:
                model = LGBMRegressor(
                    n_estimators=200,
                    max_depth=8,
                    learning_rate=0.05,
                    random_state=42,
                    verbose=-1
                )
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                metrics = self._compute_metrics(y_test, y_pred, f"{crop}_LGBM")
                results[crop] = metrics

                # Save model
                self._save_model(model, f"{crop.lower()}_model.pkl", available)

        return results

    def get_feature_importance(self, model, feature_names: List[str]) -> pd.DataFrame:
        """Extract feature importance from trained model."""
        if hasattr(model, "feature_importances_"):
            importance_df = pd.DataFrame({
                "feature": feature_names,
                "importance": model.feature_importances_
            }).sort_values("importance", ascending=False)
            return importance_df
        return pd.DataFrame()

    def print_ablation_results(self, results: Dict):
        """Print formatted ablation results."""
        print("\n" + "="*80)
        print("ABLATION STUDY RESULTS")
        print("="*80)

        for model_name, data in results.items():
            print(f"\n{model_name} ({data['num_features']} features):")
            print(f"  Best: {data['best_model']}")

            for algo, metrics in data["models"].items():
                r2 = metrics.get("test_r2", "N/A")
                mae = metrics.get("test_mae", "N/A")
                mape = metrics.get("test_mape", "N/A")
                print(f"    {algo:20s} R²={r2:6.4f}  MAE={mae:7.2f} kg/ha  MAPE={mape}%")

        print("\n" + "="*80)
