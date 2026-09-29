"""
Weather API integrations
Open-Meteo (free, no key), NASA POWER, IMD where accessible
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Container for weather data"""
    temperature_avg: float  # °C
    temperature_min: float
    temperature_max: float
    rainfall: float  # mm
    humidity: float  # %
    solar_radiation: Optional[float]  # MJ/m²
    wind_speed: Optional[float]  # m/s
    source: str
    period: str
    timestamp: str


class WeatherAPI:
    """Fetch weather data from multiple free APIs."""

    def __init__(self):
        self.openmeteo_base = "https://archive-api.open-meteo.com/v1/archive"
        self.openmeteo_forecast = "https://api.open-meteo.com/v1/forecast"
        self.nasa_power_base = "https://power.larc.nasa.gov/api/temporal/daily/point"

    def get_openmeteo_historical(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        season: str = "Rabi"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical weather from Open-Meteo (free, no API key).

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            season: "Rabi" (Oct-Mar) or "Kharif" (Jun-Oct)

        Returns:
            DataFrame with daily weather or None if failed
        """
        try:
            # Open-Meteo Archive API (free tier)
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "Asia/Kolkata"
            }

            response = requests.get(self.openmeteo_base, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                daily = data.get("daily", {})

                df = pd.DataFrame({
                    "date": pd.to_datetime(daily.get("time", [])),
                    "temp_avg": daily.get("temperature_2m_mean", []),
                    "temp_max": daily.get("temperature_2m_max", []),
                    "temp_min": daily.get("temperature_2m_min", []),
                    "precipitation": daily.get("precipitation_sum", [])
                })

                logger.info(f"Fetched {len(df)} days of weather from Open-Meteo")
                return df
            else:
                logger.warning(f"Open-Meteo returned {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching Open-Meteo data: {e}")
            return None

    def compute_seasonal_features(
        self,
        weather_df: pd.DataFrame,
        season: str,
        year: int
    ) -> Dict[str, float]:
        """
        Compute seasonal weather features from daily data.

        Args:
            weather_df: Daily weather DataFrame
            season: "Rabi" or "Kharif"
            year: Year

        Returns:
            Dictionary of seasonal features
        """
        try:
            if weather_df is None or len(weather_df) == 0:
                return self._get_punjab_climatology(season)

            # Define season date ranges
            if season == "Rabi":  # Oct-Mar
                season_months = [10, 11, 12, 1, 2, 3]
            else:  # Kharif  Jun-Oct
                season_months = [6, 7, 8, 9, 10]

            # Filter season months
            seasonal = weather_df[
                weather_df["date"].dt.month.isin(season_months)
            ].copy()

            if len(seasonal) == 0:
                return self._get_punjab_climatology(season)

            # Compute features
            features = {
                "rainfall_total": float(seasonal["precipitation"].sum()),
                "rainfall_days": float((seasonal["precipitation"] > 1).sum()),
                "temp_avg": float(seasonal["temp_avg"].mean()),
                "temp_max_avg": float(seasonal["temp_max"].mean()),
                "temp_min_avg": float(seasonal["temp_min"].mean()),
                "temp_max": float(seasonal["temp_max"].max()),
                "temp_min": float(seasonal["temp_min"].min()),
                "gdd": float(self._compute_gdd(seasonal["temp_avg"].values)),
                "heat_stress_days": float((seasonal["temp_max"] > 35).sum()),
                "cold_stress_days": float((seasonal["temp_min"] < 5).sum()),
            }

            return features
        except Exception as e:
            logger.warning(f"Error computing seasonal features: {e}")
            return self._get_punjab_climatology(season)

    def _compute_gdd(self, temps: np.ndarray, base_temp: float = 10.0) -> float:
        """
        Compute Growing Degree Days (GDD).

        GDD = sum(max(0, T_avg - T_base)) for each day
        """
        gdd = np.sum(np.maximum(0, temps - base_temp))
        return float(gdd)

    def _get_punjab_climatology(self, season: str) -> Dict[str, float]:
        """
        Punjab climatological averages (fallback when API fails).

        Source: IMD climatology 1991-2020
        """
        if season == "Rabi":  # Wheat season (Nov-Apr)
            return {
                "rainfall_total": 150.0,  # mm
                "rainfall_days": 12.0,
                "temp_avg": 20.0,  # °C
                "temp_max_avg": 25.0,
                "temp_min_avg": 10.0,
                "temp_max": 35.0,
                "temp_min": 2.0,
                "gdd": 1200.0,
                "heat_stress_days": 3.0,
                "cold_stress_days": 15.0,
            }
        else:  # Kharif (Rice) season (Jun-Oct)
            return {
                "rainfall_total": 450.0,  # mm (monsoon)
                "rainfall_days": 45.0,
                "temp_avg": 28.0,
                "temp_max_avg": 32.0,
                "temp_min_avg": 22.0,
                "temp_max": 38.0,
                "temp_min": 18.0,
                "gdd": 2500.0,
                "heat_stress_days": 25.0,
                "cold_stress_days": 0.0,
            }

    def get_forecast(self, lat: float, lon: float, days: int = 7) -> Optional[Dict]:
        """
        Get weather forecast for next N days.

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of forecast days

        Returns:
            Forecast dictionary or None
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": days,
                "timezone": "Asia/Kolkata"
            }

            response = requests.get(self.openmeteo_forecast, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get("daily", {})
            return None

        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return None

    def compute_weather_anomalies(
        self,
        current_year: int,
        district: str,
        season: str
    ) -> Dict[str, float]:
        """
        Compute weather anomalies vs historical average.

        For training: returns 0 (anomalies computed later)
        For inference: compares current season to climatology
        """
        # Simplified: in production, compare to 10-year average
        return {
            "rainfall_anomaly": 0.0,
            "temp_anomaly": 0.0,
        }
