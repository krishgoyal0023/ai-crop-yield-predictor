"""
Data cleaning utilities for yield prediction pipeline
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean and preprocess agricultural data."""

    def __init__(self):
        self.outlier_bounds = {}
        self.imputation_values = {}

    def validate_schema(self, df: pd.DataFrame, required_cols: list) -> pd.DataFrame:
        """
        Validate that DataFrame has required columns.

        Args:
            df: Input DataFrame
            required_cols: List of required column names

        Returns:
            Validated DataFrame

        Raises:
            ValueError: If required columns are missing
        """
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return df

    def remove_invalid_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove invalid values based on domain rules.

        Rules:
        - Year: 2000-2026
        - Area > 0
        - Yield > 0
        - Production >= 0 (can be 0 if area is 0, but we remove that)
        """
        initial = len(df)

        # Remove rows with invalid Year
        if "Year" in df.columns:
            df = df[(df["Year"] >= 2000) & (df["Year"] <= 2026)]

        # Remove rows with non-positive Area or Yield
        if "Area" in df.columns:
            df = df[df["Area"] > 0]
        if "Yield" in df.columns:
            df = df[df["Yield"] > 0]

        removed = initial - len(df)
        logger.info(f"Removed {removed} invalid records")
        return df

    def cap_outliers(self, df: pd.DataFrame, column: str,
                     lower_percentile: float = 0.01,
                     upper_percentile: float = 0.99) -> pd.DataFrame:
        """
        Cap outliers using percentile-based clipping.

        Args:
            df: Input DataFrame
            column: Column to cap
            lower_percentile: Lower percentile (default 1%)
            upper_percentile: Upper percentile (default 99%)

        Returns:
            DataFrame with capped values
        """
        if column not in df.columns:
            logger.warning(f"Column {column} not found, skipping outlier capping")
            return df

        q_low = df[column].quantile(lower_percentile)
        q_high = df[column].quantile(upper_percentile)

        self.outlier_bounds[column] = {"lower": q_low, "upper": q_high}

        df[column] = df[column].clip(lower=q_low, upper=q_high)
        logger.info(f"Capped {column}: [{q_low:.2f}, {q_high:.2f}]")

        return df

    def remove_duplicates(self, df: pd.DataFrame,
                         subset: list = None) -> pd.DataFrame:
        """
        Remove duplicate rows.

        Args:
            df: Input DataFrame
            subset: Columns to consider for duplicates (default: Year, District, Crop, Season)

        Returns:
            Deduplicated DataFrame
        """
        if subset is None:
            subset = ["Year", "District", "Crop", "Season"]
            subset = [col for col in subset if col in df.columns]

        initial = len(df)
        df = df.drop_duplicates(subset=subset, keep="first")
        removed = initial - len(df)

        if removed > 0:
            logger.info(f"Removed {removed} duplicate records")

        return df

    def handle_missing_values(self, df: pd.DataFrame,
                             strategy: str = "mean") -> pd.DataFrame:
        """
        Handle missing values in numeric columns.

        Args:
            df: Input DataFrame
            strategy: 'mean', 'median', 'mode', or 'drop'

        Returns:
            DataFrame with missing values handled
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if strategy == "drop":
            df = df.dropna(subset=numeric_cols)
        else:
            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    if strategy == "mean":
                        fill_value = df[col].mean()
                    elif strategy == "median":
                        fill_value = df[col].median()
                    else:
                        fill_value = df[col].mode()[0]

                    self.imputation_values[col] = fill_value
                    df[col] = df[col].fillna(fill_value)

        return df

    def normalize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize units to standard:
        - Yield: kg/ha (convert from q/ha if needed)
        - Area: hectares
        - Production: tonnes
        """
        # Convert quintals/ha to kg/ha (1 q = 100 kg)
        if "Yield" in df.columns:
            if df["Yield"].max() < 100:  # Likely in q/ha
                df["Yield"] = df["Yield"] * 100
                logger.info("Converted Yield from q/ha to kg/ha")

        return df

    def clean_pipeline(self, df: pd.DataFrame,
                      required_cols: list = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Run complete cleaning pipeline.

        Args:
            df: Input DataFrame
            required_cols: Required columns

        Returns:
            Cleaned DataFrame and cleaning report
        """
        report = {
            "initial_records": len(df),
            "steps": []
        }

        # Step 1: Validate schema
        if required_cols:
            try:
                df = self.validate_schema(df, required_cols)
                report["steps"].append("Schema validation: PASSED")
            except ValueError as e:
                logger.error(f"Schema validation failed: {e}")
                report["steps"].append(f"Schema validation: FAILED - {e}")
                return df, report

        # Step 2: Remove invalid values
        df = self.remove_invalid_values(df)
        report["steps"].append(f"Invalid values removed: {report['initial_records'] - len(df)}")
        report["records_after_invalid_removal"] = len(df)

        # Step 3: Remove duplicates
        df = self.remove_duplicates(df)
        report["steps"].append(f"Duplicates removed: {report['records_after_invalid_removal'] - len(df)}")
        report["records_after_deduplication"] = len(df)

        # Step 4: Handle missing values
        df = self.handle_missing_values(df, strategy="mean")
        report["steps"].append("Missing values imputed (mean)")

        # Step 5: Cap outliers
        if "Yield" in df.columns:
            df = self.cap_outliers(df, "Yield")
            report["steps"].append("Outliers capped (1st-99th percentile)")

        # Step 6: Normalize units
        df = self.normalize_units(df)
        report["steps"].append("Units normalized")

        report["final_records"] = len(df)
        report["total_removed"] = report["initial_records"] - len(df)

        logger.info(f"Cleaning complete: {report['initial_records']} → {report['final_records']} records")

        return df, report
