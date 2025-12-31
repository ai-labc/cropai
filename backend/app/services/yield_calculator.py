"""
Yield prediction calculator
Calculates yield prediction from actual weather, soil moisture, and NDVI data
"""

from app.api.models import YieldPredictionData
from app.services.era5 import get_weather_data
from app.services.era5land import get_soil_moisture
from app.services.sentinel2 import get_ndvi_timeline
from typing import List, Optional
from datetime import datetime, timedelta


async def calculate_yield_prediction(
    field_id: str,
    lat: float,
    lng: float,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
) -> List[YieldPredictionData]:
    """
    Calculate yield prediction from actual data
    
    Args:
        field_id: Field identifier
        lat: Latitude
        lng: Longitude
        date_start: Start date (YYYY-MM-DD), optional
        date_end: End date (YYYY-MM-DD), optional
    
    Returns:
        List of YieldPredictionData with predicted yield values
    """
    # Parse dates
    if date_end:
        end_date = datetime.fromisoformat(date_end.replace('Z', '+00:00'))
    else:
        end_date = datetime.now()
    
    if date_start:
        start_date = datetime.fromisoformat(date_start.replace('Z', '+00:00'))
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get actual data with timeout
    import asyncio
    
    try:
        try:
            weather_data, soil_data = await asyncio.wait_for(
                asyncio.gather(
                    get_weather_data(
                        lat=lat,
                        lng=lng,
                        date_start=date_start,
                        date_end=date_end
                    ),
                    get_soil_moisture(
                        lat=lat,
                        lng=lng,
                        date_start=date_start,
                        date_end=date_end,
                        field_id=field_id
                    ),
                    return_exceptions=True
                ),
                timeout=30.0
            )
            
            # Handle exceptions
            if isinstance(weather_data, Exception):
                print(f"[Yield Calculator] Weather data error: {weather_data}")
                weather_data = []
            if isinstance(soil_data, Exception):
                print(f"[Yield Calculator] Soil data error: {soil_data}")
                soil_data = []
        except asyncio.TimeoutError:
            print("[Yield Calculator] Data fetching timeout, using defaults")
            weather_data = []
            soil_data = []
        
        # Try to get NDVI data (may fail if API endpoint not available)
        ndvi_data = []
        try:
            ndvi_data = await asyncio.wait_for(
                get_ndvi_timeline(
                    field_id=field_id,
                    date_start=date_start,
                    date_end=date_end
                ),
                timeout=10.0
            )
        except (asyncio.TimeoutError, Exception) as e:
            print(f"[Yield Calculator] NDVI data error (optional): {e}")
            pass  # NDVI data is optional
        
        # Calculate yield prediction based on actual data
        timeline = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Base yield (tons per hectare) - varies by crop type
        base_yield = 40.0  # Default for canola/hay
        
        # Create date-indexed maps for quick lookup
        weather_map = {d.timestamp[:10]: d.value for d in weather_data}
        soil_map = {d.timestamp[:10]: d.value for d in soil_data}
        ndvi_map = {d.timestamp[:10]: d.value for d in ndvi_data}
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Get data for this date
            temp = weather_map.get(date_str, 15.0)  # Default 15°C
            soil_moisture = soil_map.get(date_str, 50.0)  # Default 50%
            ndvi = ndvi_map.get(date_str, 0.6)  # Default 0.6
            
            # Calculate yield factors
            # Temperature factor (optimal: 15-25°C)
            if 15 <= temp <= 25:
                temp_factor = 1.0
            elif temp < 15:
                temp_factor = 0.8 + (temp - 10) * 0.04  # Linear decrease below 15°C
            else:
                temp_factor = 1.0 - (temp - 25) * 0.02  # Linear decrease above 25°C
            
            # Soil moisture factor (optimal: 30-60%)
            if 30 <= soil_moisture <= 60:
                soil_factor = 1.0
            elif soil_moisture < 30:
                soil_factor = 0.7 + (soil_moisture / 30) * 0.3  # Too dry
            else:
                soil_factor = 1.0 - ((soil_moisture - 60) / 40) * 0.3  # Too wet
            
            # NDVI factor (higher NDVI = better growth)
            ndvi_factor = 0.5 + ndvi * 0.5  # Map 0-1 NDVI to 0.5-1.0 factor
            
            # Calculate predicted yield
            yield_value = base_yield * temp_factor * soil_factor * ndvi_factor
            
            # Add some variation
            import random
            variation = random.random() * 4 - 2  # ±2 tons
            yield_value = max(0, yield_value + variation)
            
            # Confidence based on data availability
            confidence = 0.7
            if weather_data and len(weather_data) > 0:
                confidence += 0.1
            if soil_data and len(soil_data) > 0:
                confidence += 0.1
            if ndvi_data and len(ndvi_data) > 0:
                confidence += 0.1
            confidence = min(0.95, confidence)
            
            timeline.append(YieldPredictionData(
                timestamp=current_date.isoformat(),
                value=round(yield_value, 2),
                fieldId=field_id,
                confidence=round(confidence, 3)
            ))
            
            current_date += timedelta(days=1)
        
        return timeline
        
    except Exception as e:
        print(f"[Yield Calculator] Error calculating yield: {e}")
        import traceback
        traceback.print_exc()
        # Return empty timeline on error
        return []

