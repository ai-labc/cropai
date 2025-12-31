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
        from app.api.routes.fields import get_fields
        
        # Try to get field data from fields API
        field_found = False
        field_lat = lat
        field_lng = lng
        field_crop_type = crop_type
        
        # Known field mappings
        field_data_map = {
            "field-1": {
                "lat": 52.619167,
                "lng": -113.092639,
                "crop_type": "Canola",
                "bounds": {"north": 52.624167, "south": 52.614167, "east": -113.087639, "west": -113.102639}
            },
            "field-2": {
                "lat": 52.619167,
                "lng": -113.092639,
                "crop_type": "Canola",
                "bounds": {"north": 52.624167, "south": 52.614167, "east": -113.092639, "west": -113.102639}
            },
            "field-3": {
                "lat": 54.0167,
                "lng": -124.0167,
                "crop_type": "Timothy Hay",
                "bounds": {"north": 54.02167, "south": 54.01167, "east": -124.01167, "west": -124.02167}
            },
            "field-4": {
                "lat": 54.0167,
                "lng": -124.0167,
                "crop_type": "Timothy Hay",
                "bounds": {"north": 54.02167, "south": 54.01167, "east": -124.01667, "west": -124.02667}
            }
        }
        
        # Check known fields first
        if field_id in field_data_map:
            field_data = field_data_map[field_id]
            field_lat = lat if lat is not None else field_data["lat"]
            field_lng = lng if lng is not None else field_data["lng"]
            field_crop_type = crop_type if crop_type else field_data["crop_type"]
            bounds = field_data["bounds"]
            field_found = True
        else:
            # Try to extract farm_id and crop_id from field_id pattern (e.g., field-farm-1-crop-2)
            import re
            farm_match = re.search(r'farm-(\d+)', field_id)
            crop_match = re.search(r'crop-(\d+)', field_id)
            
            if farm_match and crop_match:
                # Extract farm_id and crop_id from field_id
                search_farm_id = f"farm-{farm_match.group(1)}"
                search_crop_id = f"crop-{crop_match.group(1)}"
                
                try:
                    fields_response = await get_fields(search_farm_id, search_crop_id)
                    print(f"[Stress Index] Searching for field {field_id} in farm {search_farm_id}, crop {search_crop_id}")
                    if fields_response.status == "success":
                        print(f"[Stress Index] Found {len(fields_response.data)} fields: {[f.id for f in fields_response.data]}")
                        for field in fields_response.data:
                            print(f"[Stress Index] Checking field: {field.id} (looking for {field_id})")
                            if field.id == field_id:
                                # Extract location from field geometry
                                if field.geometry and field.geometry.get("coordinates"):
                                    coords = field.geometry["coordinates"][0]
                                    lngs = [c[0] for c in coords]
                                    lats = [c[1] for c in coords]
                                    field_lat = (max(lats) + min(lats)) / 2
                                    field_lng = (max(lngs) + min(lngs)) / 2
                                    bounds = {
                                        "north": max(lats),
                                        "south": min(lats),
                                        "east": max(lngs),
                                        "west": min(lngs)
                                    }
                                    print(f"[Stress Index] ✓ Found field {field_id} from fields API")
                                    print(f"[Stress Index] Using geometry bounds: north={bounds['north']:.6f}, south={bounds['south']:.6f}, east={bounds['east']:.6f}, west={bounds['west']:.6f}")
                                    print(f"[Stress Index] Field center: lat={field_lat:.6f}, lng={field_lng:.6f}")
                                else:
                                    # Geometry exists but no coordinates - use farm location with default bounds
                                    if search_farm_id == "farm-1":
                                        field_lat, field_lng = 52.619167, -113.092639
                                        # Use default bounds based on farm location (not crop-specific)
                                        bounds = {"north": 52.624167, "south": 52.614167, "east": -113.087639, "west": -113.102639}
                                    else:
                                        field_lat, field_lng = 54.0167, -124.0167
                                        bounds = {"north": 54.02167, "south": 54.01167, "east": -124.01167, "west": -124.02167}
                                
                                # Determine crop type
                                if search_crop_id == "crop-1":
                                    field_crop_type = crop_type if crop_type else "Canola"
                                else:
                                    field_crop_type = crop_type if crop_type else "Timothy Hay"
                                
                                field_found = True
                                break
                        if not field_found:
                            print(f"[Stress Index] ✗ Field {field_id} not found in fields response")
                except Exception as e:
                    print(f"[Stress Index] Error fetching fields for {search_farm_id}/{search_crop_id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # No fallback search - only use exact farm/crop combination
            # This prevents finding wrong fields from other combinations
        
        # If still not found, use defaults based on farm location (not crop)
        if not field_found:
            import re
            farm_match = re.search(r'farm-(\d+)', field_id)
            crop_match = re.search(r'crop-(\d+)', field_id)
            
            # Use farm location - each farm's crops should be displayed at that farm's location
            if farm_match:
                farm_num = farm_match.group(1)
                if farm_num == "1":
                    # farm-1 (AB) - use AB location
                    field_lat = lat if lat is not None else 52.619167
                    field_lng = lng if lng is not None else -113.092639
                    bounds = {"north": 52.624167, "south": 52.614167, "east": -113.087639, "west": -113.102639}
                else:
                    # farm-2 (BC) - use BC location
                    field_lat = lat if lat is not None else 54.0167
                    field_lng = lng if lng is not None else -124.0167
                    bounds = {"north": 54.02167, "south": 54.01167, "east": -124.01167, "west": -124.02167}
            else:
                # Default to farm-1 location (AB)
                field_lat = lat if lat is not None else 52.619167
                field_lng = lng if lng is not None else -113.092639
                bounds = {"north": 52.624167, "south": 52.614167, "east": -113.087639, "west": -113.102639}
            
            # Determine crop type
            if crop_match:
                crop_num = crop_match.group(1)
                field_crop_type = crop_type if crop_type else ("Canola" if crop_num == "1" else "Timothy Hay")
            else:
                field_crop_type = crop_type if crop_type else "Canola"
        
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

