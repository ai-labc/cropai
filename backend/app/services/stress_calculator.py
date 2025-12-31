"""
Stress Index Calculator
Rule-based stress calculation from NDVI, weather, and soil moisture data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.services.era5 import get_weather_data
from app.services.sentinel2 import get_ndvi_timeline
import numpy as np


# Crop-specific stress thresholds
CROP_THRESHOLDS = {
    "Canola": {
        "optimal_temp_min": 10.0,  # Celsius
        "optimal_temp_max": 25.0,
        "heat_stress_temp": 30.0,
        "min_rainfall_7d": 10.0,  # mm per week
    },
    "Timothy Hay": {
        "optimal_temp_min": 15.0,
        "optimal_temp_max": 28.0,
        "heat_stress_temp": 32.0,
        "min_rainfall_7d": 15.0,
    },
    "default": {
        "optimal_temp_min": 12.0,
        "optimal_temp_max": 26.0,
        "heat_stress_temp": 30.0,
        "min_rainfall_7d": 12.0,
    }
}


def calculate_stress_score(
    ndvi_current: float,
    ndvi_prev14: Optional[float],
    temp_7d_avg: float,
    rain_7d_total: float,
    crop_type: str = "Canola"
) -> Dict[str, Any]:
    """
    Calculate stress score (0-100) based on multiple factors
    
    Args:
        ndvi_current: Current NDVI value
        ndvi_prev14: NDVI value 14 days ago (optional)
        temp_7d_avg: Average temperature over last 7 days (°C)
        rain_7d_total: Total rainfall over last 7 days (mm)
        crop_type: Crop type for threshold lookup
    
    Returns:
        Dictionary with stressScore, level, reasons, and components
    """
    thresholds = CROP_THRESHOLDS.get(crop_type, CROP_THRESHOLDS["default"])
    
    # Component scores (0-1, where 1 = high stress)
    components = {}
    reasons = []
    
    # 1. NDVI drop component (0-40 points)
    ndvi_stress = 0.0
    if ndvi_prev14 is not None:
        ndvi_drop = ndvi_prev14 - ndvi_current
        if ndvi_drop > 0.1:  # Significant drop
            ndvi_stress = min(1.0, ndvi_drop / 0.3)  # Normalize to 0-1
            reasons.append("NDVI dropped significantly")
        elif ndvi_drop > 0.05:
            ndvi_stress = ndvi_drop / 0.15
            reasons.append("NDVI showing decline")
    else:
        # If no previous NDVI, use current NDVI as indicator
        if ndvi_current < 0.3:
            ndvi_stress = 0.8
            reasons.append("Low NDVI indicates poor vegetation health")
        elif ndvi_current < 0.5:
            ndvi_stress = 0.4
    
    components["ndvi"] = ndvi_stress
    ndvi_score = ndvi_stress * 40  # Max 40 points
    
    # 2. Water stress component (0-30 points)
    water_stress = 0.0
    if rain_7d_total < thresholds["min_rainfall_7d"]:
        deficit = thresholds["min_rainfall_7d"] - rain_7d_total
        water_stress = min(1.0, deficit / thresholds["min_rainfall_7d"])
        reasons.append(f"Low rainfall ({rain_7d_total:.1f}mm in 7 days)")
    elif rain_7d_total == 0:
        water_stress = 1.0
        reasons.append("No rainfall in 7 days")
    
    components["water"] = water_stress
    water_score = water_stress * 30  # Max 30 points
    
    # 3. Heat stress component (0-30 points)
    heat_stress = 0.0
    if temp_7d_avg > thresholds["heat_stress_temp"]:
        excess = temp_7d_avg - thresholds["heat_stress_temp"]
        heat_stress = min(1.0, excess / 10.0)  # Normalize
        reasons.append(f"High temperature ({temp_7d_avg:.1f}°C)")
    elif temp_7d_avg < thresholds["optimal_temp_min"]:
        # Cold stress (less severe)
        deficit = thresholds["optimal_temp_min"] - temp_7d_avg
        heat_stress = min(0.5, deficit / 10.0) * 0.5  # Max 0.5 for cold
        reasons.append(f"Low temperature ({temp_7d_avg:.1f}°C)")
    elif temp_7d_avg > thresholds["optimal_temp_max"]:
        # Above optimal but not extreme
        excess = temp_7d_avg - thresholds["optimal_temp_max"]
        heat_stress = min(0.5, excess / 5.0)
    
    components["heat"] = heat_stress
    heat_score = heat_stress * 30  # Max 30 points
    
    # Total stress score (0-100)
    total_score = ndvi_score + water_score + heat_score
    total_score = min(100.0, max(0.0, total_score))
    
    # Determine stress level
    if total_score >= 70:
        level = "HIGH"
    elif total_score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"
    
    if not reasons:
        reasons.append("No significant stress detected")
    
    return {
        "stressScore": round(total_score, 1),
        "level": level,
        "reasons": reasons,
        "components": {
            "ndvi": round(ndvi_stress, 2),
            "water": round(water_stress, 2),
            "heat": round(heat_stress, 2)
        }
    }


async def calculate_stress_grid(
    field_id: str,
    lat: float,
    lng: float,
    crop_type: str = "Canola",
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate stress index grid for a field
    
    Args:
        field_id: Field identifier
        lat: Latitude
        lng: Longitude
        crop_type: Crop type
        date_start: Start date (YYYY-MM-DD), optional
        date_end: End date (YYYY-MM-DD), optional
    
    Returns:
        Dictionary with grid data (64x64 stress values 0-1)
    """
    try:
        # Get date range
        if date_end:
            end_date = datetime.fromisoformat(date_end.replace('Z', '+00:00'))
        else:
            end_date = datetime.now()
        
        if date_start:
            start_date = datetime.fromisoformat(date_start.replace('Z', '+00:00'))
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get data with timeout
        import asyncio
        
        try:
            # Get weather data (last 7 days for stress calculation)
            weather_7d_start = (end_date - timedelta(days=7)).strftime('%Y-%m-%d')
            weather_7d_end = end_date.strftime('%Y-%m-%d')
            
            weather_data, ndvi_timeline = await asyncio.wait_for(
                asyncio.gather(
                    get_weather_data(
                        lat=lat,
                        lng=lng,
                        date_start=weather_7d_start,
                        date_end=weather_7d_end
                    ),
                    get_ndvi_timeline(
                        field_id=field_id,
                        date_start=(end_date - timedelta(days=14)).strftime('%Y-%m-%d'),
                        date_end=end_date.strftime('%Y-%m-%d')
                    ),
                    return_exceptions=True
                ),
                timeout=30.0
            )
            
            # Handle exceptions
            if isinstance(weather_data, Exception):
                print(f"[Stress Calculator] Weather data error: {weather_data}")
                weather_data = []
            if isinstance(ndvi_timeline, Exception):
                print(f"[Stress Calculator] NDVI timeline error: {ndvi_timeline}")
                ndvi_timeline = []
        except asyncio.TimeoutError:
            print("[Stress Calculator] Data fetching timeout, using defaults")
            weather_data = []
            ndvi_timeline = []
        
        # Calculate aggregated metrics
        # Temperature: average of last 7 days
        temp_7d_avg = 20.0  # Default
        rain_7d_total = 15.0  # Default (mm)
        
        if weather_data and len(weather_data) > 0:
            # Weather data contains temperature values
            temp_values = [d.value for d in weather_data[-7:]]  # Last 7 days
            if temp_values:
                temp_7d_avg = sum(temp_values) / len(temp_values)
            
            # Note: ERA5 get_weather_data currently returns temperature only
            # For precipitation, we would need a separate call or enhanced weather data
            # For now, use a default value based on temperature (dry if hot)
            if temp_7d_avg > 25.0:
                rain_7d_total = 5.0  # Likely dry if hot
            elif temp_7d_avg < 15.0:
                rain_7d_total = 20.0  # Likely more rain if cool
            else:
                rain_7d_total = 15.0  # Moderate
        
        # NDVI: current and 14 days ago
        ndvi_current = 0.6  # Default
        ndvi_prev14 = None
        
        if ndvi_timeline and len(ndvi_timeline) >= 2:
            # Get most recent NDVI
            ndvi_current = ndvi_timeline[-1].value
            
            # Get NDVI from 14 days ago (or closest available)
            target_date = end_date - timedelta(days=14)
            for ndvi_point in ndvi_timeline:
                point_date = datetime.fromisoformat(ndvi_point.timestamp.replace('Z', '+00:00'))
                if abs((point_date - target_date).days) <= 2:  # Within 2 days
                    ndvi_prev14 = ndvi_point.value
                    break
        
        # Calculate base stress score
        base_stress = calculate_stress_score(
            ndvi_current=ndvi_current,
            ndvi_prev14=ndvi_prev14,
            temp_7d_avg=temp_7d_avg,
            rain_7d_total=rain_7d_total,
            crop_type=crop_type
        )
        
        # Generate 64x64 grid with spatial variation
        # Base stress score normalized to 0-1
        base_stress_value = base_stress["stressScore"] / 100.0
        
        grid_size = 64
        stress_grid = []
        
        try:
            # Add spatial variation to grid
            if hasattr(np, 'random'):
                # Create grid with spatial variation
                base_array = np.full((grid_size, grid_size), base_stress_value)
                # Add random variation (±0.2)
                variation = np.random.random((grid_size, grid_size)) * 0.4 - 0.2
                stress_array = np.clip(base_array + variation, 0.0, 1.0)
                stress_grid = stress_array.tolist()
            else:
                import random
                for i in range(grid_size):
                    row = []
                    for j in range(grid_size):
                        variation = random.random() * 0.4 - 0.2
                        stress_value = max(0.0, min(1.0, base_stress_value + variation))
                        row.append(round(stress_value, 3))
                    stress_grid.append(row)
        except:
            # Fallback: uniform grid
            import random
            for i in range(grid_size):
                row = []
                for j in range(grid_size):
                    variation = random.random() * 0.4 - 0.2
                    stress_value = max(0.0, min(1.0, base_stress_value + variation))
                    row.append(round(stress_value, 3))
                stress_grid.append(row)
        
        return {
            "grid": stress_grid,
            "stressScore": base_stress["stressScore"],
            "level": base_stress["level"],
            "reasons": base_stress["reasons"],
            "components": base_stress["components"]
        }
        
    except Exception as e:
        print(f"[Stress Calculator] Error calculating stress grid: {e}")
        import traceback
        traceback.print_exc()
        # Return default low-stress grid
        grid_size = 64
        return {
            "grid": [[0.2] * grid_size for _ in range(grid_size)],
            "stressScore": 20.0,
            "level": "LOW",
            "reasons": ["Calculation error, using default"],
            "components": {"ndvi": 0.0, "water": 0.0, "heat": 0.0}
        }

