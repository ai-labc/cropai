"""
NDVI/EVI endpoints
"""

from fastapi import APIRouter, HTTPException
from app.api.models import NDVIGrid, APIResponse, TimeSeriesData
from app.services.sentinel2 import calculate_ndvi, get_ndvi_timeline
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()


class NDVICalculationRequest(BaseModel):
    field_id: str
    geometry: Dict[str, Any]  # GeoJSON geometry
    date_start: str
    date_end: str


@router.post("/ndvi/calculate", response_model=APIResponse[NDVIGrid])
async def calculate_ndvi_endpoint(request: NDVICalculationRequest):
    """
    Calculate NDVI for a field polygon and date range
    """
    try:
        ndvi_grid = await calculate_ndvi(
            field_id=request.field_id,
            geometry=request.geometry,
            date_start=request.date_start,
            date_end=request.date_end
        )
        return APIResponse(
            data=ndvi_grid,
            timestamp="2024-01-01T00:00:00Z",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ndvi/{field_id}/timeline", response_model=APIResponse[List[TimeSeriesData]])
async def get_ndvi_timeline_endpoint(
    field_id: str,
    date_start: str = None,
    date_end: str = None
):
    """
    Get NDVI timeline (average/median) for a field
    """
    try:
        timeline = await get_ndvi_timeline(
            field_id=field_id,
            date_start=date_start,
            date_end=date_end
        )
        return APIResponse(
            data=timeline,
            timestamp="2024-01-01T00:00:00Z",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ndvi/{field_id}/grid", response_model=APIResponse[NDVIGrid])
async def get_ndvi_grid_endpoint(field_id: str, date: str = None):
    """
    Get NDVI grid for a field (latest available or specific date)
    
    Implementation:
    1. Get field geometry from field_id
    2. Calculate bbox from geometry
    3. Search Sentinel-2 products (with cloud filter)
    4. Download and process bands
    5. Apply polygon mask
    6. Calculate NDVI = (NIR - Red) / (NIR + Red)
    7. Downsample to 64x64 grid
    8. Return grid JSON with stats
    """
    try:
        from datetime import datetime, timedelta
        from app.services.sentinel2 import calculate_ndvi
        from app.api.models import GridData, GridBounds
        from app.services.geometry_service import get_field_geometry_with_fallback
        import numpy as np
        
        # Step 1: Get field geometry from shared geometry service (single source of truth)
        # This ensures NDVI uses the exact same geometry as the boundaries endpoint
        field_geometry = get_field_geometry_with_fallback(field_id)
        
        if not field_geometry:
            raise HTTPException(
                status_code=404,
                detail=f"Field geometry not found for field_id: {field_id}"
            )
        
        # Step 2: Calculate bbox from geometry
        if field_geometry.get("type") == "Polygon" and field_geometry.get("coordinates"):
            coords = field_geometry["coordinates"][0]  # First ring
            lngs = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            bbox = GridBounds(
                north=max(lats),
                south=min(lats),
                east=max(lngs),
                west=min(lngs)
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid field geometry")
        
        # Step 3-7: Calculate NDVI (using existing calculate_ndvi function)
        # Use recent date range (last 30 days) if date not specified
        if date:
            date_start = date
            date_end = date
        else:
            end_date = datetime.now()
            date_end = end_date.strftime("%Y-%m-%d")
            date_start = (end_date - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Call calculate_ndvi which handles:
        # - Sentinel-2 product search (with cloud filter)
        # - Download and processing
        # - Polygon masking
        # - NDVI calculation
        ndvi_result = await calculate_ndvi(
            field_id=field_id,
            geometry=field_geometry,
            date_start=date_start,
            date_end=date_end
        )
        
        # Step 7: Downsample to 64x64 if needed
        grid_values = ndvi_result.grid.values
        current_height = len(grid_values)
        current_width = len(grid_values[0]) if current_height > 0 else 0
        
        target_size = 64
        
        if current_height != target_size or current_width != target_size:
            # Downsample using numpy if available
            try:
                grid_array = np.array(grid_values, dtype=np.float32)
                if grid_array.size > 0:
                    # Simple block averaging downsampling (no scipy dependency)
                    step_y = max(1, current_height // target_size)
                    step_x = max(1, current_width // target_size)
                    
                    new_grid = np.zeros((target_size, target_size), dtype=np.float32)
                    for i in range(target_size):
                        for j in range(target_size):
                            y_start = min(i * step_y, current_height - 1)
                            y_end = min((i + 1) * step_y, current_height)
                            x_start = min(j * step_x, current_width - 1)
                            x_end = min((j + 1) * step_x, current_width)
                            
                            block = grid_array[y_start:y_end, x_start:x_end]
                            valid_values = block[block != 0]  # Exclude masked values
                            if len(valid_values) > 0:
                                new_grid[i, j] = float(np.mean(valid_values))
                            else:
                                new_grid[i, j] = 0.0
                    
                    grid_values = new_grid.tolist()
            except (ImportError, AttributeError):
                # Fallback: Simple downsampling without scipy
                step_y = max(1, current_height // target_size)
                step_x = max(1, current_width // target_size)
                grid_values = [
                    [grid_values[i * step_y][j * step_x] 
                     for j in range(0, current_width, step_x)][:target_size]
                    for i in range(0, current_height, step_y)
                ][:target_size]
        
        # Calculate statistics
        all_values = [val for row in grid_values for val in row if val is not None]
        if all_values:
            stats = {
                "mean": float(np.mean(all_values)) if hasattr(np, 'mean') else sum(all_values) / len(all_values),
                "median": float(np.median(all_values)) if hasattr(np, 'median') else sorted(all_values)[len(all_values) // 2],
                "min": float(min(all_values)),
                "max": float(max(all_values))
            }
        else:
            stats = {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
        
        # Create grid response
        grid = GridData(
            resolution=ndvi_result.grid.resolution,
            bounds=bbox,
            values=grid_values
        )
        
        ndvi_grid = NDVIGrid(
            fieldId=field_id,
            timestamp=datetime.now().isoformat(),
            grid=grid
        )
        
        return APIResponse(
            data=ndvi_grid,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error calculating NDVI grid: {str(e)}")

