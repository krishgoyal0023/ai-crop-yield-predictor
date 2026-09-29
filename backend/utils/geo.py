"""
Geospatial utilities
District lookup from lat/lon, coordinate transformations, spatial joins
"""

import json
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# Punjab district boundaries (centroid lat/lon)
# Source: Punjab government, Census of India
PUNJAB_DISTRICTS = {
    "Amritsar": {"lat": 31.6340, "lon": 74.8733, "region": "Central"},
    "Bathinda": {"lat": 30.2110, "lon": 74.9455, "region": "Southwestern"},
    "Faridkot": {"lat": 30.6783, "lon": 74.7408, "region": "Southwestern"},
    "Fatehgarh Sahib": {"lat": 30.6425, "lon": 76.3928, "region": "Central"},
    "Ferozepur": {"lat": 30.9167, "lon": 74.6167, "region": "Southwestern"},
    "Gurdaspur": {"lat": 32.0400, "lon": 75.4000, "region": "Northeastern"},
    "Hoshiarpur": {"lat": 31.5400, "lon": 75.9100, "region": "Northeastern"},
    "Jalandhar": {"lat": 31.3260, "lon": 75.5760, "region": "Central"},
    "Kapurthala": {"lat": 31.3800, "lon": 75.3800, "region": "Central"},
    "Ludhiana": {"lat": 30.9010, "lon": 75.8573, "region": "Central"},
    "Mansa": {"lat": 29.9900, "lon": 75.3900, "region": "Southwestern"},
    "Moga": {"lat": 30.8220, "lon": 75.1700, "region": "Southwestern"},
    "Muktsar": {"lat": 30.4740, "lon": 74.5150, "region": "Southwestern"},
    "Nawanshahr": {"lat": 31.1200, "lon": 76.1200, "region": "Northeastern"},
    "Patiala": {"lat": 30.3300, "lon": 76.4000, "region": "Southern"},
    "Rupnagar": {"lat": 30.9700, "lon": 76.5300, "region": "Northeastern"},
    "Sangrur": {"lat": 30.2500, "lon": 75.8400, "region": "Southern"},
    "SAS Nagar": {"lat": 30.7000, "lon": 76.6900, "region": "Northeastern"},
    "Tarn Taran": {"lat": 31.4500, "lon": 74.9300, "region": "Central"},
    "Barnala": {"lat": 30.3700, "lon": 75.5400, "region": "Southern"},
}

# Punjab geographic bounds
PUNJAB_BOUNDS = {
    "min_lat": 29.5,
    "max_lat": 32.5,
    "min_lon": 73.5,
    "max_lon": 76.8
}


def find_district_from_coords(lat: float, lon: float) -> Optional[str]:
    """
    Find the nearest Punjab district from coordinates.

    Uses simple distance to district centroids.
    In production, use proper point-in-polygon with GeoJSON.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        District name or None if outside Punjab
    """
    min_dist = float('inf')
    nearest_district = None

    for district, coords in PUNJAB_DISTRICTS.items():
        # Simple Euclidean distance (good enough for Punjab ~100km scale)
        dist = ((lat - coords["lat"])**2 + (lon - coords["lon"])**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest_district = district

    # Only return if within reasonable distance (< 0.5 degrees ~ 55km)
    if min_dist < 0.5:
        return nearest_district
    return None


def is_in_punjab(lat: float, lon: float) -> bool:
    """
    Check if coordinates are within Punjab state bounds.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        True if within Punjab, False otherwise
    """
    return (
        PUNJAB_BOUNDS["min_lat"] <= lat <= PUNJAB_BOUNDS["max_lat"]
        and PUNJAB_BOUNDS["min_lon"] <= lon <= PUNJAB_BOUNDS["max_lon"]
    )


def get_district_info(district: str) -> Optional[Dict]:
    """
    Get district information including coordinates and region.

    Args:
        district: District name

    Returns:
        Dictionary with district info or None
    """
    return PUNJAB_DISTRICTS.get(district)


def get_region(district: str) -> Optional[str]:
    """
    Get agro-climatic region for a district.

    Args:
        district: District name

    Returns:
        Region name or None
    """
    info = PUNJAB_DISTRICTS.get(district)
    return info["region"] if info else None


def compute_elevation(lat: float, lon: float) -> float:
    """
    Estimate elevation from coordinates.
    Punjab is relatively flat (200-300m above sea level).

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Estimated elevation in meters
    """
    # Simplified: Punjab elevation range 180-300m
    # In production, use SRTM or Google Elevation API
    base_elevation = 240.0

    # Add some spatial variation (higher in northeast, lower in southwest)
    lat_factor = (lat - 30.5) * 20  # Higher in north
    lon_factor = (lon - 75.0) * 10  # Higher in east

    elevation = base_elevation + lat_factor + lon_factor
    return max(180, min(320, elevation))


def load_geojson() -> Optional[Dict]:
    """
    Load Punjab district GeoJSON for map display.

    Returns:
        GeoJSON dictionary or None
    """
    geojson_path = Path(__file__).parent.parent.parent / "data" / "punjab_districts.geojson"

    if geojson_path.exists():
        with open(geojson_path, "r") as f:
            return json.load(f)

    return None


def generate_simple_geojson() -> Dict:
    """
    Generate a simple GeoJSON with district centroids.
    For actual boundaries, download from data.gov.in or GADM.
    """
    features = []

    for district, info in PUNJAB_DISTRICTS.items():
        feature = {
            "type": "Feature",
            "properties": {
                "name": district,
                "region": info["region"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [info["lon"], info["lat"]]
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }
