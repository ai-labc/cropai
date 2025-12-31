"""
Weather data endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from app.api.models import TimeSeriesData, APIResponse
from app.services.era5 import get_weather_data
from app.services.precompute import get_precomputed_data, precompute_weather
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/weather/{field_id}", response_model=APIResponse[List[TimeSeriesData]])
async def get_weather(
    field_id: str,
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    date_start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get weather data (temperature, precipitation, etc.) for a field location
    Uses precomputed JSON if available, otherwise computes on-demand
    """
    try:
        # Default to last 30 days if dates not provided
        if not date_end:
            date_end = datetime.now().strftime("%Y-%m-%d")
        if not date_start:
            date_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Try to get precomputed data first (only if using default 30-day range)
        use_precomputed = (
            date_start == (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d") and
            date_end == datetime.now().strftime("%Y-%m-%d")
        )
        
        if use_precomputed:
            key = f"{field_id}_{lat:.4f}_{lng:.4f}"
            precomputed = get_precomputed_data("weather", key)
            
            if precomputed and precomputed.get("data"):
                # Convert dict back to TimeSeriesData objects
                from app.api.models import TimeSeriesData
                weather_data_list = [TimeSeriesData(**item) for item in precomputed["data"]]
                # Return precomputed data
                return APIResponse(
                    data=weather_data_list,
                    timestamp=precomputed.get("computed_at", datetime.now().isoformat()),
                    status="success"
                )
        
        # Fallback to on-demand calculation
        weather_data = await get_weather_data(
            lat=lat,
            lng=lng,
            date_start=date_start,
            date_end=date_end
        )
        
        # Optionally trigger background precomputation for next time (if using default range)
        if use_precomputed:
            try:
                import asyncio
                asyncio.create_task(precompute_weather(field_id, lat, lng))
            except:
                pass  # Silently fail background precomputation
        
        return APIResponse(
            data=weather_data,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

