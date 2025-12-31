"""
Carbon metrics endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from app.api.models import CarbonMetricsData, APIResponse
from app.services.carbon_calculator import calculate_carbon_metrics
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/carbon-metrics/{field_id}", response_model=APIResponse[List[CarbonMetricsData]])
async def get_carbon_metrics(
    field_id: str,
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    date_start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get carbon metrics data for a field
    Uses actual weather and NDVI data for calculation
    
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
        
        # Calculate carbon metrics from actual data
        carbon_data = await calculate_carbon_metrics(
            field_id=field_id,
            lat=lat,
            lng=lng,
            date_start=date_start,
            date_end=date_end
        )
        
        return APIResponse(
            data=carbon_data,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

