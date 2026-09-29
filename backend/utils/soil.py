"""
Soil data integration
SoilGrids API (ISRIC) - free, no key required
Falls back to Punjab-specific synthetic data
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SoilAPI:
    """Fetch soil data from SoilGrids API."""

    def __init__(self):
        self.soilgrids_base = "https://rest.soilgrids.org/query"

    def get_soil_properties(
        self,
        lat: float,
        lon: float
    ) -> Optional[Dict[str, float]]:
        """
        Fetch soil properties from SoilGrids API.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary of soil properties or None
        """
        try:
            # SoilGrids REST API (free, no key)
            params = {
                "lon": lon,
                "lat": lat,
                "property": "phh2o,soc,bdod,clay,sand,silt,cec,nitrogen,phosphorus,potassium",
                "depth": "0-5cm",
                "value": "mean"
            }

            response = requests.get(self.soilgrids_base, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                properties = self._parse_soilgrids_response(data)
                logger.info("Fetched soil data from SoilGrids")
                return properties
            else:
                logger.warning(f"SoilGrids returned {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching SoilGrids data: {e}")
            return None

    def _parse_soilgrids_response(self, data: Dict) -> Dict[str, float]:
        """Parse SoilGrids API response."""
        properties = {}

        # SoilGrids returns properties with specific names
        mapping = {
            "phh2o": "pH",
            "soc": "SOC",  # Soil organic carbon (g/kg)
            "bdod": "BD",  # Bulk density
            "clay": "Clay",
            "sand": "Sand",
            "silt": "Silt"
        }

        for key, value in data.items():
            if key in mapping:
                # Convert units if needed
                if key == "soc":  # g/kg to %
                    properties[mapping[key]] = value / 10.0
                elif key in ["clay", "sand", "silt"]:  # g/kg to %
                    properties[mapping[key]] = value / 10.0
                else:
                    properties[mapping[key]] = value

        return properties

    def get_district_soil_fallback(
        self,
        district: str,
        state: str = "Punjab"
    ) -> Dict[str, float]:
        """
        Fallback: return district-level soil averages for Punjab.

        Based on Punjab soil survey data (ICAR-CSSRI):
        - pH: 7.0-8.5 (alkaline)
        - SOC: 0.5-1.2%
        - Texture: Sandy loam to loam
        """
        # Punjab-specific averages by district region
        soil_profiles = {
            "central": {  # Ludhiana, Jalandhar, Kapurthala
                "pH": 7.5,
                "SOC": 0.8,
                "Clay": 25.0,
                "Sand": 50.0,
                "Silt": 25.0,
                "N": 180.0,
                "P": 18.0,
                "K": 250.0,
            },
            "southwestern": {  # Bathinda, Faridkot, Mansa
                "pH": 8.2,
                "SOC": 0.5,
                "Clay": 20.0,
                "Sand": 60.0,
                "Silt": 20.0,
                "N": 150.0,
                "P": 12.0,
                "K": 200.0,
            },
            "northeastern": {  # Gurdaspur, Hoshiarpur, Pathankot
                "pH": 6.8,
                "SOC": 1.0,
                "Clay": 30.0,
                "Sand": 40.0,
                "Silt": 30.0,
                "N": 200.0,
                "P": 22.0,
                "K": 300.0,
            },
            "southern": {  # Patiala, Sangrur, Barnala
                "pH": 7.8,
                "SOC": 0.7,
                "Clay": 22.0,
                "Sand": 55.0,
                "Silt": 23.0,
                "N": 160.0,
                "P": 15.0,
                "K": 220.0,
            },
        }

        # Map district to region
        district_region_map = {
            "Ludhiana": "central", "Jalandhar": "central", "Kapurthala": "central",
            "Bathinda": "southwestern", "Faridkot": "southwestern", "Mansa": "southwestern",
            "Muktsar": "southwestern", "Gurdaspur": "northeastern", "Hoshiarpur": "northeastern",
            "Patiala": "southern", "Sangrur": "southern", "Barnala": "southern",
        }

        region = district_region_map.get(district, "central")

        # Add some randomness to simulate field-level variation
        soil = soil_profiles[region].copy()
        for key in soil:
            soil[key] *= np.random.uniform(0.9, 1.1)

        return soil

    def classify_soil_type(self, clay: float, sand: float, silt: float) -> str:
        """
        Classify soil type based on USDA texture triangle.

        Args:
            clay: Clay percentage
            sand: Sand percentage
            silt: Silt percentage

        Returns:
            Soil texture class
        """
        if clay >= 40:
            if sand >= 45:
                return "Sandy Clay"
            elif silt >= 40:
                return "Silty Clay"
            else:
                return "Clay"

        elif clay >= 27:
            if sand >= 20 and sand <= 45:
                return "Clay Loam"
            elif sand > 45:
                return "Sandy Clay Loam"
            else:
                return "Silty Clay Loam"

        elif clay >= 12:
            if sand >= 52:
                return "Loamy Sand"
            elif sand >= 28 and sand <= 50:
                return "Loam"
            elif silt >= 50:
                return "Silt Loam"
            else:
                return "Silt"

        else:  # clay < 12
            if sand >= 70:
                return "Sand"
            elif sand >= 50:
                return "Loamy Sand"
            else:
                return "Silt Loam"
