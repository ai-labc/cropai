"""
Service for loading field boundary GeoJSON files
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from app.api.models import FieldBoundary

# Path to the fields data directory
FIELDS_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "fields"


def load_field_from_file(field_id: str) -> Optional[Dict]:
    """
    Load a single field GeoJSON file
    
    Args:
        field_id: Field ID (e.g., "field-1")
    
    Returns:
        GeoJSON feature dict or None if not found
    """
    file_path = FIELDS_DATA_DIR / f"{field_id}.geojson"
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Convert GeoJSON Feature to FieldBoundary format
        if geojson_data.get("type") == "Feature":
            return {
                "id": geojson_data.get("id", field_id),
                "farmId": geojson_data.get("properties", {}).get("farmId"),
                "cropId": geojson_data.get("properties", {}).get("cropId"),
                "geometry": geojson_data.get("geometry"),
                "properties": geojson_data.get("properties", {})
            }
        return None
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading field {field_id}: {e}")
        return None


def load_fields_by_farm_crop(farm_id: str, crop_id: str) -> List[Dict]:
    """
    Load all fields matching farm_id and crop_id from GeoJSON files
    
    Args:
        farm_id: Farm ID (e.g., "farm-1")
        crop_id: Crop ID (e.g., "crop-1")
    
    Returns:
        List of field boundary dicts
    """
    fields = []
    
    if not FIELDS_DATA_DIR.exists():
        return fields
    
    # Scan all .geojson files in the directory
    for geojson_file in FIELDS_DATA_DIR.glob("*.geojson"):
        try:
            with open(geojson_file, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            if geojson_data.get("type") != "Feature":
                continue
            
            props = geojson_data.get("properties", {})
            if props.get("farmId") == farm_id and props.get("cropId") == crop_id:
                fields.append({
                    "id": geojson_data.get("id", geojson_file.stem),
                    "farmId": props.get("farmId"),
                    "cropId": props.get("cropId"),
                    "geometry": geojson_data.get("geometry"),
                    "properties": props
                })
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading field from {geojson_file}: {e}")
            continue
    
    return fields


def load_all_fields() -> List[Dict]:
    """
    Load all field GeoJSON files from the data directory
    
    Returns:
        List of all field boundary dicts
    """
    fields = []
    
    if not FIELDS_DATA_DIR.exists():
        return fields
    
    for geojson_file in FIELDS_DATA_DIR.glob("*.geojson"):
        try:
            with open(geojson_file, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            if geojson_data.get("type") == "Feature":
                fields.append({
                    "id": geojson_data.get("id", geojson_file.stem),
                    "farmId": geojson_data.get("properties", {}).get("farmId"),
                    "cropId": geojson_data.get("properties", {}).get("cropId"),
                    "geometry": geojson_data.get("geometry"),
                    "properties": geojson_data.get("properties", {})
                })
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading field from {geojson_file}: {e}")
            continue
    
    return fields

