"""
Soil moisture endpoints (Optional for MVP)
"""

from fastapi import APIRouter, HTTPException, Query
from app.api.models import SoilMoistureData, APIResponse
from app.services.era5land import get_soil_moisture
from app.services.precompute import get_precomputed_data, precompute_soil_moisture
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/soil-moisture/{field_id}", response_model=APIResponse[List[SoilMoistureData]])
async def get_soil_moisture_endpoint(
    field_id: str,
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    date_start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get soil moisture data from ERA5-Land (Optional for MVP)
    Uses precomputed JSON if available, otherwise computes on-demand
    """
    try:
        # Use default location if not provided (Hartland Colony, Alberta)
        if lat is None:
            lat = 52.619167  # Hartland Colony, Alberta
        if lng is None:
            lng = -113.092639
        
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
            precomputed = get_precomputed_data("soil", key)
            
            if precomputed and precomputed.get("data"):
                # Convert dict back to SoilMoistureData objects
                soil_data_list = [SoilMoistureData(**item) for item in precomputed["data"]]
                # Return precomputed data
                return APIResponse(
                    data=soil_data_list,
                    timestamp=precomputed.get("computed_at", datetime.now().isoformat()),
                    status="success"
                )
        
        # Fallback to on-demand calculation
        soil_data = await get_soil_moisture(
            lat=lat,
            lng=lng,
            date_start=date_start,
            date_end=date_end,
            field_id=field_id
        )
        
        # Optionally trigger background precomputation for next time (if using default range)
        if use_precomputed:
            try:
                import asyncio
                asyncio.create_task(precompute_soil_moisture(field_id, lat, lng))
            except:
                pass  # Silently fail background precomputation
        
        return APIResponse(
            data=soil_data,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

