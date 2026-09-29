"""
Data loader and cleaning module
Handles loading, cleaning, and validation of agricultural datasets
for Punjab Wheat and Rice yield prediction.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and validate Punjab agricultural datasets."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def load_yield_data(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Load crop yield data from data.gov.in (DES Punjab).

        Expected columns: Year, District, Crop, Season, Area (ha), Production (tonnes), Yield (kg/ha)

        Returns:
            DataFrame with standardized yield data
        """
        if filepath is None:
            filepath = self.data_dir / "punjab_yield.csv"

        if not Path(filepath).exists():
            logger.warning(f"Yield data not found at {filepath}. Using synthetic data.")
            return self._generate_synthetic_yield_data()

        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} yield records")
        return df

    def _generate_synthetic_yield_data(self) -> pd.DataFrame:
        """
        Generate realistic synthetic yield data for Punjab (2010-2023)
        Wheat and Rice across major districts.

        Based on real DES Punjab statistics:
        - Wheat yield: ~4.5-5.5 t/ha (increasing trend)
        - Rice yield: ~3.8-4.5 t/ha (increasing trend)
        """
        np.random.seed(42)

        districts = [
            "Amritsar", "Bathinda", "Faridkot", "Fatehgarh Sahib",
            "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
            "Kapurthala", "Ludhiana", "Mansa", "Moga",
            "Muktsar", "Nawanshahr", "Patiala", "Rupnagar",
            "Sangrur", "SAS Nagar", "Tarn Taran", "Barnala"
        ]

        crops = {
            "Wheat": {
                "base_yield": 4800,  # kg/ha
                "trend": 80,  # kg/ha per year
                "noise": 400,
                "season": "Rabi"
            },
            "Rice": {
                "base_yield": 4100,
                "trend": 60,
                "noise": 350,
                "season": "Kharif"
            }
        }

        records = []

        for year in range(2010, 2024):
            for district in districts:
                # District-specific multipliers (realistic variation)
                district_factor = np.random.uniform(0.85, 1.15)

                for crop_name, params in crops.items():
                    yield_kg = (
                        params["base_yield"]
                        + params["trend"] * (year - 2010)
                        + np.random.normal(0, params["noise"])
                    ) * district_factor

                    # Ensure non-negative
                    yield_kg = max(yield_kg, 2500)

                    area = np.random.uniform(10000, 80000)  # hectares

                    records.append({
                        "Year": year,
                        "District": district,
                        "Crop": crop_name,
                        "Season": params["season"],
                        "Area": area,
                        "Production": (yield_kg * area) / 1000,  # tonnes
                        "Yield": yield_kg,  # kg/ha
                        "district_factor": district_factor
                    })

        df = pd.DataFrame(records)
        logger.info(f"Generated {len(df)} synthetic yield records (2010-2023)")
        return df

    def clean_yield_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate yield data.

        Rules:
        - Remove rows with Year < 2000 or Year > current
        - Remove rows with Area <= 0
        - Remove rows with Yield <= 0
        - Cap extreme outliers (>99th percentile, <1st percentile)
        - Remove duplicates
        """
        initial_count = len(df)

        # 1. Remove invalid years
        df = df[(df["Year"] >= 2000) & (df["Year"] <= 2026)]

        # 2. Remove invalid area
        df = df[df["Area"] > 0]

        # 3. Remove invalid yield
        df = df[df["Yield"] > 0]

        # 4. Remove duplicates
        df = df.drop_duplicates(subset=["Year", "District", "Crop", "Season"])

        # 5. Cap extreme outliers (1st and 99th percentiles)
        for crop in df["Crop"].unique():
            mask = df["Crop"] == crop
            q1 = df.loc[mask, "Yield"].quantile(0.01)
            q99 = df.loc[mask, "Yield"].quantile(0.99)
            df.loc[mask & (df["Yield"] < q1), "Yield"] = q1
            df.loc[mask & (df["Yield"] > q99), "Yield"] = q99

        logger.info(
            f"Cleaned yield data: {initial_count} → {len(df)} records "
            f"({initial_count - len(df)} removed)"
        )

        return df

    def load_soil_data(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Load soil data (from SoilGrids or synthetic).

        Expected columns: District, pH, SOC, N, P, K, Clay, Sand, Silt
        """
        if filepath and Path(filepath).exists():
            return pd.read_csv(filepath)

        # Generate synthetic soil data for Punjab
        np.random.seed(123)

        districts = [
            "Amritsar", "Bathinda", "Faridkot", "Fatehgarh Sahib",
            "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
            "Kapurthala", "Ludhiana", "Mansa", "Moga",
            "Muktsar", "Nawanshahr", "Patiala", "Rupnagar",
            "Sangrur", "SAS Nagar", "Tarn Taran", "Barnala"
        ]

        soil_data = []

        for district in districts:
            # Punjab soil characteristics (sandy loam to loam, pH 7-8.5)
            soil_data.append({
                "District": district,
                "pH": np.random.uniform(7.0, 8.5),
                "SOC": np.random.uniform(0.5, 1.2),  # % organic carbon
                "N": np.random.uniform(100, 250),  # kg/ha
                "P": np.random.uniform(10, 30),  # kg/ha
                "K": np.random.uniform(150, 400),  # kg/ha
                "Clay": np.random.uniform(15, 35),  # %
                "Sand": np.random.uniform(40, 65),  # %
                "Silt": np.random.uniform(15, 30),  # %
                "Elevation": np.random.uniform(200, 300),  # m
            })

        df = pd.DataFrame(soil_data)
        logger.info(f"Generated synthetic soil data for {len(df)} districts")
        return df

    def validate_data_quality(self, df: pd.DataFrame) -> dict:
        """
        Generate data quality report.

        Returns:
            Dictionary with quality metrics
        """
        report = {
            "total_records": len(df),
            "date_range": f"{df['Year'].min()}-{df['Year'].max()}" if "Year" in df else "N/A",
            "districts": df["District"].nunique() if "District" in df else 0,
            "crops": df["Crop"].unique().tolist() if "Crop" in df else [],
            "missing_values": df.isnull().sum().to_dict(),
            "duplicates": df.duplicated().sum(),
            "yield_stats": {
                "mean": df["Yield"].mean() if "Yield" in df else None,
                "std": df["Yield"].std() if "Yield" in df else None,
                "min": df["Yield"].min() if "Yield" in df else None,
                "max": df["Yield"].max() if "Yield" in df else None,
            } if "Yield" in df else {}
        }

        return report
