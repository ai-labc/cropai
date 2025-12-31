"""
Yield prediction endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from app.api.models import YieldPredictionData, APIResponse
from app.services.yield_calculator import calculate_yield_prediction
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/yield-prediction/{field_id}", response_model=APIResponse[List[YieldPredictionData]])
async def get_yield_prediction(
    field_id: str,
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    date_start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get yield prediction data for a field
    Uses actual weather, soil moisture, and NDVI data for calculation
    
    Args:
        field_id: Field identifier
        lat: Latitude (optional, will use default if not provided)
        lng: Longitude (optional, will use default if not provided)
        date_start: Start date (YYYY-MM-DD), optional
        date_end: End date (YYYY-MM-DD), optional
    """
    try:
        # Use default location if not provided (Hartland Colony, Alberta)
        if lat is None:
            lat = 52.619167
        if lng is None:
            lng = -113.092639
        
        # Calculate yield prediction from actual data
        yield_data = await calculate_yield_prediction(
            field_id=field_id,
            lat=lat,
            lng=lng,
            date_start=date_start,
            date_end=date_end
        )
        
        return APIResponse(
            data=yield_data,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

