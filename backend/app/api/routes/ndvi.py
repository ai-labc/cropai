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
        from app.api.routes.fields import get_fields
        from app.services.sentinel2 import calculate_ndvi
        from app.api.models import GridData, GridBounds
        import numpy as np
        
        # Step 1: Get field geometry from field_id
        # Direct field data lookup (same as fields.py)
        field_geometry = None
        
        # Field data mapping (same structure as fields.py)
        field_data_map = {
            "field-1": {
                "farm_id": "farm-1",
                "crop_id": "crop-1",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-113.097639, 52.614167],  # SW
                        [-113.087639, 52.614167],  # SE
                        [-113.087639, 52.624167],  # NE
                        [-113.097639, 52.624167],  # NW
                        [-113.097639, 52.614167]   # Close polygon
                    ]]
                }
            },
            "field-2": {
                "farm_id": "farm-1",
                "crop_id": "crop-1",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-113.102639, 52.614167],
                        [-113.092639, 52.614167],
                        [-113.092639, 52.624167],
                        [-113.102639, 52.624167],
                        [-113.102639, 52.614167]
                    ]]
                }
            },
            "field-3": {
                "farm_id": "farm-2",
                "crop_id": "crop-2",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-124.02167, 54.01167],  # SW
                        [-124.01167, 54.01167],  # SE
                        [-124.01167, 54.02167],  # NE
                        [-124.02167, 54.02167],  # NW
                        [-124.02167, 54.01167]   # Close polygon
                    ]]
                }
            },
            "field-4": {
                "farm_id": "farm-2",
                "crop_id": "crop-2",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-124.02667, 54.01167],
                        [-124.01667, 54.01167],
                        [-124.01667, 54.02167],
                        [-124.02667, 54.02167],
                        [-124.02667, 54.01167]
                    ]]
                }
            }
        }
        
        if field_id in field_data_map:
            field_geometry = field_data_map[field_id]["geometry"]
        else:
            # Fallback: try to get from fields endpoint
            try:
                field_to_farm_crop = {
                    "field-1": ("farm-1", "crop-1"),
                    "field-2": ("farm-1", "crop-1"),
                    "field-3": ("farm-2", "crop-2"),
                    "field-4": ("farm-2", "crop-2"),
                }
                if field_id in field_to_farm_crop:
                    farm_id, crop_id = field_to_farm_crop[field_id]
                    fields_response = await get_fields(farm_id, crop_id)
                    if fields_response.status == "success":
                        for field in fields_response.data:
                            if field.id == field_id:
                                field_geometry = field.geometry
                                break
            except Exception as e:
                print(f"[NDVI Grid] Error fetching fields: {e}")
        
        # If field not found, try to get from fields API
        # First, try to extract farm_id and crop_id from field_id pattern (e.g., field-farm-1-crop-2)
        if not field_geometry:
            import re
            farm_match = re.search(r'farm-(\d+)', field_id)
            crop_match = re.search(r'crop-(\d+)', field_id)
            
            if farm_match and crop_match:
                # Extract farm_id and crop_id from field_id
                farm_id = f"farm-{farm_match.group(1)}"
                crop_id = f"crop-{crop_match.group(1)}"
                
                try:
                    fields_response = await get_fields(farm_id, crop_id)
                    if fields_response.status == "success":
                        print(f"[NDVI Grid] Searching for field {field_id} in farm {farm_id}, crop {crop_id}")
                        print(f"[NDVI Grid] Available fields: {[f.id for f in fields_response.data]}")
                        for field in fields_response.data:
                            if field.id == field_id:
                                field_geometry = field.geometry
                                # Log geometry bounds for debugging
                                if field_geometry and field_geometry.get("coordinates"):
                                    coords = field_geometry["coordinates"][0]
                                    lngs = [c[0] for c in coords]
                                    lats = [c[1] for c in coords]
                                    print(f"[NDVI Grid] Found field {field_id} from fields API")
                                    print(f"[NDVI Grid] Geometry bounds: lat=[{min(lats):.6f}, {max(lats):.6f}], lng=[{min(lngs):.6f}, {max(lngs):.6f}]")
                                break
                except Exception as e:
                    print(f"[NDVI Grid] Error fetching fields for {farm_id}/{crop_id}: {e}")
            
            # No fallback search - only use exact farm/crop combination
            # This prevents finding wrong fields from other combinations
        
        # If still not found, use default bounds based on farm location (not crop)
        if not field_geometry:
            print(f"[NDVI Grid] Field {field_id} not found in database, using default bounds based on farm location")
            import re
            farm_match = re.search(r'farm-(\d+)', field_id)
            
            # Use farm location - each farm's crops should be displayed at that farm's location
            if farm_match:
                farm_num = farm_match.group(1)
                if farm_num == "1":
                    base_lat, base_lng = 52.619167, -113.092639  # farm-1 (AB) - Hartland Colony
                else:
                    base_lat, base_lng = 54.0167, -124.0167  # farm-2 (BC) - Exceedagro
            else:
                # Default to farm-1 location (AB)
                base_lat, base_lng = 52.619167, -113.092639
            
            # Create default geometry
            field_geometry = {
                "type": "Polygon",
                "coordinates": [[
                    [base_lng - 0.005, base_lat - 0.005],
                    [base_lng + 0.005, base_lat - 0.005],
                    [base_lng + 0.005, base_lat + 0.005],
                    [base_lng - 0.005, base_lat + 0.005],
                    [base_lng - 0.005, base_lat - 0.005]
                ]]
            }
        
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

