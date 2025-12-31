"""
Stress Index endpoints
Rule-based stress calculation from NDVI, weather, and soil moisture data
"""

from fastapi import APIRouter, HTTPException, Query
from app.api.models import StressIndex, APIResponse, GridData
from app.services.stress_calculator import calculate_stress_grid
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/stress/{field_id}", response_model=APIResponse[StressIndex])
async def get_stress_index_endpoint(
    field_id: str,
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    crop_type: Optional[str] = Query(None, description="Crop type (Canola, Timothy Hay, etc.)")
):
    """
    Get stress index grid for a field
    Stress index indicates crop stress levels (water, heat, NDVI decline)
    Calculated from actual NDVI, weather, and soil moisture data
    """
    try:
        from app.services.geometry_service import get_field_geometry_with_fallback, get_farm_anchor
        
        # Get field geometry from shared geometry service (single source of truth)
        # This ensures Stress uses the exact same geometry as Boundaries and NDVI
        field_geometry = get_field_geometry_with_fallback(field_id)
        
        if not field_geometry or not field_geometry.get("coordinates"):
            raise HTTPException(
                status_code=404,
                detail=f"Field geometry not found for field_id: {field_id}"
            )
        
        # Extract bounds and center from geometry
        coords = field_geometry["coordinates"][0]  # First ring
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        bounds = {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs)
        }
        
        # Calculate center point
        field_lat = lat if lat is not None else (max(lats) + min(lats)) / 2
        field_lng = lng if lng is not None else (max(lngs) + min(lngs)) / 2
        
        # Determine crop type from field_id pattern if not provided
        if not crop_type:
            import re
            crop_match = re.search(r'crop-(\d+)', field_id)
            if crop_match:
                crop_num = crop_match.group(1)
                field_crop_type = "Canola" if crop_num == "1" else "Timothy Hay"
            else:
                # Default based on farm location
                farm_match = re.search(r'farm-(\d+)', field_id)
                if farm_match:
                    farm_num = farm_match.group(1)
                    field_crop_type = "Canola" if farm_num == "1" else "Timothy Hay"
                else:
                    field_crop_type = "Canola"  # Default
        else:
            field_crop_type = crop_type
        
        # Calculate stress grid from actual data
        stress_result = await calculate_stress_grid(
            field_id=field_id,
            lat=field_lat,
            lng=field_lng,
            crop_type=field_crop_type
        )
        
        grid = GridData(
            bounds=bounds,
            resolution=0.02,
            values=stress_result["grid"]
        )
        
        stress_index = StressIndex(
            fieldId=field_id,
            timestamp=datetime.now().isoformat(),
            grid=grid
        )
        
        return APIResponse(
            data=stress_index,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

