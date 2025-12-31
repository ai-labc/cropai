"""
Precompute service for generating JSON files of KPI, Weather, and Soil data
Runs in background to pre-calculate data for faster API responses
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path
from app.config import settings
from app.services.kpi_calculator import calculate_kpi_summary
from app.services.era5 import get_weather_data
from app.services.era5land import get_soil_moisture


# Precomputed data directory
PRECOMPUTE_DIR = os.path.join(settings.cache_dir, "precomputed")
os.makedirs(PRECOMPUTE_DIR, exist_ok=True)


def get_precompute_path(data_type: str, key: str) -> str:
    """Get file path for precomputed data"""
    return os.path.join(PRECOMPUTE_DIR, f"{data_type}_{key}.json")


async def precompute_kpi(farm_id: str, crop_id: str, field_id: str = None, lat: float = None, lng: float = None) -> Dict[str, Any]:
    """
    Precompute KPI summary for a farm/crop combination
    
    Args:
        farm_id: Farm identifier
        crop_id: Crop identifier
        field_id: Optional field identifier
        lat: Optional latitude
        lng: Optional longitude
    
    Returns:
        Precomputed KPI data
    """
    try:
        kpi_data = await calculate_kpi_summary(
            farm_id=farm_id,
            crop_id=crop_id,
            field_id=field_id,
            lat=lat,
            lng=lng
        )
        
        # Create cache key
        key_parts = [farm_id, crop_id]
        if field_id:
            key_parts.append(field_id)
        if lat and lng:
            key_parts.append(f"{lat:.4f}_{lng:.4f}")
        key = "_".join(key_parts)
        
        # Save to JSON file
        file_path = get_precompute_path("kpi", key)
        data = {
            "farm_id": farm_id,
            "crop_id": crop_id,
            "field_id": field_id,
            "lat": lat,
            "lng": lng,
            "data": kpi_data,
            "computed_at": datetime.now().isoformat(),
            "ttl_hours": 24  # Valid for 24 hours
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"[Precompute] Error computing KPI for {farm_id}/{crop_id}: {e}")
        return None


async def precompute_weather(field_id: str, lat: float, lng: float, days: int = 30) -> Dict[str, Any]:
    """
    Precompute weather data for a location
    
    Args:
        field_id: Field identifier
        lat: Latitude
        lng: Longitude
        days: Number of days to compute
    
    Returns:
        Precomputed weather data
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        weather_data = await get_weather_data(
            lat=lat,
            lng=lng,
            date_start=start_date.strftime("%Y-%m-%d"),
            date_end=end_date.strftime("%Y-%m-%d")
        )
        
        # Create cache key
        key = f"{field_id}_{lat:.4f}_{lng:.4f}"
        
        # Save to JSON file
        file_path = get_precompute_path("weather", key)
        data = {
            "field_id": field_id,
            "lat": lat,
            "lng": lng,
            "data": weather_data,
            "computed_at": datetime.now().isoformat(),
            "ttl_hours": 6  # Valid for 6 hours (weather changes frequently)
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"[Precompute] Error computing weather for {field_id}: {e}")
        return None


async def precompute_soil_moisture(field_id: str, lat: float, lng: float, days: int = 30) -> Dict[str, Any]:
    """
    Precompute soil moisture data for a location
    
    Args:
        field_id: Field identifier
        lat: Latitude
        lng: Longitude
        days: Number of days to compute
    
    Returns:
        Precomputed soil moisture data
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        soil_data = await get_soil_moisture(
            lat=lat,
            lng=lng,
            date_start=start_date.strftime("%Y-%m-%d"),
            date_end=end_date.strftime("%Y-%m-%d"),
            field_id=field_id
        )
        
        # Create cache key
        key = f"{field_id}_{lat:.4f}_{lng:.4f}"
        
        # Convert Pydantic models to dict for JSON serialization
        soil_data_dict = [item.model_dump() if hasattr(item, 'model_dump') else item.dict() if hasattr(item, 'dict') else item for item in soil_data]
        
        # Save to JSON file
        file_path = get_precompute_path("soil", key)
        data = {
            "field_id": field_id,
            "lat": lat,
            "lng": lng,
            "data": soil_data_dict,
            "computed_at": datetime.now().isoformat(),
            "ttl_hours": 12  # Valid for 12 hours
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"[Precompute] Error computing soil moisture for {field_id}: {e}")
        return None


def get_precomputed_data(data_type: str, key: str) -> Dict[str, Any] | None:
    """
    Get precomputed data from JSON file if valid
    
    Args:
        data_type: Type of data (kpi, weather, soil)
        key: Cache key
    
    Returns:
        Precomputed data or None if not found/expired
    """
    file_path = get_precompute_path(data_type, key)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check TTL
        computed_at = datetime.fromisoformat(data.get("computed_at", "2000-01-01T00:00:00"))
        ttl_hours = data.get("ttl_hours", 24)
        age_hours = (datetime.now() - computed_at).total_seconds() / 3600
        
        if age_hours > ttl_hours:
            # Expired, delete file
            os.remove(file_path)
            return None
        
        return data
    except Exception as e:
        print(f"[Precompute] Error reading precomputed data: {e}")
        return None


async def precompute_all_fields():
    """
    Precompute data for all known fields
    This should be called periodically (e.g., via cron or scheduler)
    """
    # Known fields from fields.py
    fields = [
        {"field_id": "field-1", "farm_id": "farm-1", "crop_id": "crop-1", "lat": 52.619167, "lng": -113.092639},
        {"field_id": "field-2", "farm_id": "farm-1", "crop_id": "crop-1", "lat": 52.619167, "lng": -113.092639},
        {"field_id": "field-3", "farm_id": "farm-2", "crop_id": "crop-2", "lat": 54.0167, "lng": -124.0167},
        {"field_id": "field-4", "farm_id": "farm-2", "crop_id": "crop-2", "lat": 54.0167, "lng": -124.0167},
    ]
    
    print(f"[Precompute] Starting precomputation for {len(fields)} fields...")
    
    for field in fields:
        field_id = field["field_id"]
        farm_id = field["farm_id"]
        crop_id = field["crop_id"]
        lat = field["lat"]
        lng = field["lng"]
        
        print(f"[Precompute] Computing data for {field_id}...")
        
        # Precompute KPI
        try:
            await precompute_kpi(farm_id, crop_id, field_id, lat, lng)
        except Exception as e:
            print(f"[Precompute] KPI error for {field_id}: {e}")
        
        # Precompute Weather
        try:
            await precompute_weather(field_id, lat, lng)
        except Exception as e:
            print(f"[Precompute] Weather error for {field_id}: {e}")
        
        # Precompute Soil Moisture
        try:
            await precompute_soil_moisture(field_id, lat, lng)
        except Exception as e:
            print(f"[Precompute] Soil error for {field_id}: {e}")
    
    print("[Precompute] Precomputation complete!")


if __name__ == "__main__":
    # Run precomputation
    import asyncio
    asyncio.run(precompute_all_fields())

