"""
Feature engineering for crop yield prediction
Generates all features needed for the ML models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Generate features for yield prediction model."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.feature_stats = {}  # Store for inference-time normalization

    def engineer_features(
        self,
        df: pd.DataFrame,
        soil_df: pd.DataFrame,
        is_training: bool = True
    ) -> pd.DataFrame:
        """
        Main feature engineering pipeline.

        Args:
            df: Yield DataFrame with Year, District, Crop, Season, Area, Yield
            soil_df: Soil properties DataFrame
            is_training: If True, compute and store feature statistics

        Returns:
            DataFrame with engineered features
        """
        df = df.copy()

        # Step 1: Basic features
        df = self._add_basic_features(df)

        # Step 2: Historical features
        df = self._add_historical_features(df, is_training)

        # Step 3: Soil features
        df = self._add_soil_features(df, soil_df)

        # Step 4: Geographic features
        df = self._add_geographic_features(df)

        # Step 5: Interaction features
        df = self._add_interaction_features(df)

        # Step 6: Encode categorical features
        df = self._encode_categoricals(df, is_training)

        logger.info(f"Engineered {len(df.columns)} features")
        return df

    def _add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic non-temporal features."""
        # Crop encoding
        df["Crop_Code"] = (df["Crop"] == "Rice").astype(int)

        # Season encoding
        df["Season_Code"] = (df["Season"] == "Kharif").astype(int)

        # Area transformations
        df["log_Area"] = np.log1p(df["Area"])

        # Year as numeric
        df["Year_Numeric"] = df["Year"].astype(int)

        # Decade
        df["Decade"] = (df["Year"] // 10) * 10

        return df

    def _add_historical_features(self, df: pd.DataFrame, is_training: bool) -> pd.DataFrame:
        """
        Add historical yield features.

        IMPORTANT: Only uses data from BEFORE the current year.
        Prevents data leakage.
        """
        df = df.copy()

        # At inference time, "Yield" may not exist yet.
        # Use district-crop baselines as proxy for lags/MA.
        has_yield = "Yield" in df.columns

        if has_yield:
            df = df.sort_values(["District", "Crop", "Year"])

            # Previous year yield (lag 1)
            df["Yield_Lag1"] = df.groupby(["District", "Crop"])["Yield"].shift(1)

            # 3-year moving average (computed from previous years only)
            df["Yield_MA3"] = df.groupby(["District", "Crop"])["Yield"].transform(
                lambda x: x.shift(1).rolling(3, min_periods=1).mean()
            )

            # 5-year moving average
            df["Yield_MA5"] = df.groupby(["District", "Crop"])["Yield"].transform(
                lambda x: x.shift(1).rolling(5, min_periods=1).mean()
            )

            # Yield trend (slope of last 5 years)
            def compute_trend(group):
                group = group.sort_values("Year")
                if len(group) >= 3:
                    y = group["Yield"].values[-5:]
                    x = np.arange(len(y))
                    if len(x) > 1 and np.std(y) > 0:
                        slope = np.polyfit(x, y, 1)[0]
                    else:
                        slope = 0
                else:
                    slope = 0
                return pd.Series(slope, index=group.index)

            df["Yield_Trend"] = df.groupby(["District", "Crop"]).apply(compute_trend).reset_index(level=[0,1], drop=True)

            # Deviation from district average
            district_crop_avg = df.groupby(["District", "Crop"])["Yield"].transform("mean")
            df["Yield_Deviation"] = df["Yield"] - district_crop_avg
        else:
            # Inference mode: fill historical features with district baselines / 0
            district_means = self.feature_stats.get("district_means", {})
            df["Yield_Lag1"] = df["District"].map(lambda d: district_means.get(d, 0))
            df["Yield_MA3"] = df["Yield_Lag1"]
            df["Yield_MA5"] = df["Yield_Lag1"]
            df["Yield_Trend"] = 0.0
            df["Yield_Deviation"] = 0.0

        # Previous crop (rotation effect) — still works without Yield
        df["Previous_Crop"] = df.groupby(["District", "Year"])["Crop"].shift(1)
        df["Is_Rice_After_Wheat"] = (
            (df["Crop"] == "Rice") & (df["Previous_Crop"] == "Wheat")
        ).astype(int)
        df["Is_Wheat_After_Rice"] = (
            (df["Crop"] == "Wheat") & (df["Previous_Crop"] == "Rice")
        ).astype(int)

        # Years of data available for this district-crop pair
        df["District_Crop_History"] = df.groupby(["District", "Crop"]).cumcount() + 1

        return df

    def _add_soil_features(self, df: pd.DataFrame, soil_df: pd.DataFrame) -> pd.DataFrame:
        """Merge soil features."""
        if soil_df is not None and len(soil_df) > 0:
            df = df.merge(soil_df, on="District", how="left")
        else:
            # Fill with Punjab averages
            soil_defaults = {
                "pH": 7.5, "SOC": 0.7, "N": 170, "P": 16, "K": 230,
                "Clay": 24, "Sand": 52, "Silt": 24, "Elevation": 240
            }
            for col, val in soil_defaults.items():
                if col not in df.columns:
                    df[col] = val

        # Soil quality index (composite)
        if "pH" in df.columns and "SOC" in df.columns:
            # pH score (optimal 6.5-7.5 for wheat, 5.5-6.5 for rice)
            df["pH_Score"] = df.apply(
                lambda row: self._score_ph(row["pH"], row["Crop"]), axis=1
            )
            df["SOC_Score"] = (df["SOC"] / 1.5).clip(0, 1)  # Normalize to 0-1

            df["Soil_Quality"] = (df["pH_Score"] + df["SOC_Score"]) / 2

        return df

    def _score_ph(self, ph: float, crop: str) -> float:
        """Score pH suitability (0-1) for a crop."""
        if crop == "Wheat":
            # Optimal 6.0-7.5
            if 6.0 <= ph <= 7.5:
                return 1.0
            elif 5.5 <= ph < 6.0 or 7.5 < ph <= 8.0:
                return 0.7
            else:
                return 0.3
        else:  # Rice
            # Optimal 5.5-7.0
            if 5.5 <= ph <= 7.0:
                return 1.0
            elif 5.0 <= ph < 5.5 or 7.0 < ph <= 7.5:
                return 0.7
            else:
                return 0.3

    def _add_geographic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add geographic features from district centroids."""
        district_info = {
            "Amritsar": {"lat": 31.634, "lon": 74.873, "elev": 234},
            "Bathinda": {"lat": 30.211, "lon": 74.946, "elev": 210},
            "Faridkot": {"lat": 30.678, "lon": 74.741, "elev": 215},
            "Fatehgarh Sahib": {"lat": 30.643, "lon": 76.393, "elev": 260},
            "Ferozepur": {"lat": 30.917, "lon": 74.617, "elev": 205},
            "Gurdaspur": {"lat": 32.040, "lon": 75.400, "elev": 290},
            "Hoshiarpur": {"lat": 31.540, "lon": 75.910, "elev": 295},
            "Jalandhar": {"lat": 31.326, "lon": 75.576, "elev": 240},
            "Kapurthala": {"lat": 31.380, "lon": 75.380, "elev": 230},
            "Ludhiana": {"lat": 30.901, "lon": 75.857, "elev": 247},
            "Mansa": {"lat": 29.990, "lon": 75.390, "elev": 200},
            "Moga": {"lat": 30.822, "lon": 75.170, "elev": 220},
            "Muktsar": {"lat": 30.474, "lon": 74.515, "elev": 195},
            "Nawanshahr": {"lat": 31.120, "lon": 76.120, "elev": 270},
            "Patiala": {"lat": 30.330, "lon": 76.400, "elev": 250},
            "Rupnagar": {"lat": 30.970, "lon": 76.530, "elev": 280},
            "Sangrur": {"lat": 30.250, "lon": 75.840, "elev": 235},
            "SAS Nagar": {"lat": 30.700, "lon": 76.690, "elev": 275},
            "Tarn Taran": {"lat": 31.450, "lon": 74.930, "elev": 225},
            "Barnala": {"lat": 30.370, "lon": 75.540, "elev": 230},
        }

        if "District" in df.columns:
            df["Latitude"] = df["District"].map(lambda x: district_info.get(x, {}).get("lat", 30.5))
            df["Longitude"] = df["District"].map(lambda x: district_info.get(x, {}).get("lon", 75.5))
            df["Elevation"] = df["District"].map(lambda x: district_info.get(x, {}).get("elev", 240))

        # Region encoding
        region_map = {
            "Amritsar": "Central", "Jalandhar": "Central", "Kapurthala": "Central",
            "Ludhiana": "Central", "Tarn Taran": "Central",
            "Bathinda": "Southwestern", "Faridkot": "Southwestern", "Mansa": "Southwestern",
            "Moga": "Southwestern", "Muktsar": "Southwestern", "Ferozepur": "Southwestern",
            "Gurdaspur": "Northeastern", "Hoshiarpur": "Northeastern", "Nawanshahr": "Northeastern",
            "Rupnagar": "Northeastern", "SAS Nagar": "Northeastern",
            "Patiala": "Southern", "Sangrur": "Southern", "Barnala": "Southern",
            "Fatehgarh Sahib": "Central"
        }

        df["Region"] = df["District"].map(region_map).fillna("Central")

        return df

    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features between important variables."""
        # Crop-Season interaction (crop type matters with season timing)
        df["Crop_Season"] = df["Crop"] + "_" + df["Season"]

        # Soil-crop interaction
        if "pH" in df.columns and "SOC" in df.columns:
            df["pH_SOC"] = df["pH"] * df["SOC"]

        # Historical trend interaction
        if "Yield_Trend" in df.columns:
            df["Trend_Crop"] = df["Yield_Trend"] * df["Crop_Code"]

        return df

    def _encode_categoricals(self, df: pd.DataFrame, is_training: bool) -> pd.DataFrame:
        """Encode categorical features."""
        # District encoding (target encoding for training, simple for inference)
        if is_training and "District" in df.columns:
            district_means = df.groupby("District")["Yield"].mean()
            df["District_Encoded"] = df["District"].map(district_means)
            self.feature_stats["district_means"] = district_means.to_dict()
        elif "District" in df.columns and "district_means" in self.feature_stats:
            df["District_Encoded"] = df["District"].map(
                self.feature_stats["district_means"]
            ).fillna(df["Yield"].mean() if "Yield" in df.columns else 4000)

        # Region one-hot
        if "Region" in df.columns:
            region_dummies = pd.get_dummies(df["Region"], prefix="Region", drop_first=True)
            df = pd.concat([df, region_dummies], axis=1)

        # Crop-Season one-hot
        if "Crop_Season" in df.columns:
            cs_dummies = pd.get_dummies(df["Crop_Season"], prefix="CS", drop_first=True)
            df = pd.concat([df, cs_dummies], axis=1)

        return df

    def get_feature_list(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of feature columns (exclude targets and non-predictive columns).

        Returns:
            List of feature column names
        """
        exclude_cols = {
            "Year", "District", "Crop", "Season", "Area", "Production", "Yield",
            "Production_yield", "district_factor", "Previous_Crop",
            "Crop_Season", "Region"
        }

        features = [col for col in df.columns if col not in exclude_cols]
        return features

    def prepare_inference_features(self, farmer_input: Dict) -> pd.DataFrame:
        """
        Prepare features for a single prediction request.

        Args:
            farmer_input: Dictionary with farmer-provided data

        Returns:
            Single-row DataFrame with all features
        """
        # This is called at inference time
        # farmer_input contains: district, crop, season, year, area, etc.
        # Weather and soil are auto-derived and added separately

        row = {
            "Year": farmer_input.get("year", 2024),
            "District": farmer_input.get("district", "Ludhiana"),
            "Crop": farmer_input.get("crop", "Wheat"),
            "Season": farmer_input.get("season", "Rabi"),
            "Area": farmer_input.get("area", 1.0),
        }

        df = pd.DataFrame([row])
        return df
