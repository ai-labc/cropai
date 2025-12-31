"""
Field boundary endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from app.api.models import FieldBoundary, APIResponse
from app.services.geometry_service import get_field_geometry_by_id, get_farm_anchor, make_bbox_polygon

router = APIRouter()


@router.get("/fields", response_model=APIResponse[List[FieldBoundary]])
async def get_fields(farm_id: str, crop_id: str):
    """
    Get field boundaries for a farm and crop
    Always returns geometry for each field (single source of truth)
    """
    # Real field data based on farm and crop
    # Farm 1: Hartland Colony (Alberta) - Canola
    # Farm 2: Exceedagro Reference Field (BC) - Timothy Hay
    
    fields = []
    
    if farm_id == "farm-1" and crop_id == "crop-1":
        # Hartland Colony - Canola fields
        # Use geometry service to ensure consistency
        field1_geometry = get_field_geometry_by_id("field-1")
        field2_geometry = get_field_geometry_by_id("field-2")
        
        fields = [
            {
                "id": "field-1",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": field1_geometry,
                "properties": {
                    "area": 25.5,
                    "cropType": "Canola"
                }
            },
            {
                "id": "field-2",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": field2_geometry,
                "properties": {
                    "area": 30.2,
                    "cropType": "Canola"
                }
            }
        ]
    elif farm_id == "farm-2" and crop_id == "crop-2":
        # Exceedagro Reference Field - Timothy Hay fields
        # Use geometry service to ensure consistency
        field3_geometry = get_field_geometry_by_id("field-3")
        field4_geometry = get_field_geometry_by_id("field-4")
        
        fields = [
            {
                "id": "field-3",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": field3_geometry,
                "properties": {
                    "area": 18.7,
                    "cropType": "Timothy Hay"
                }
            },
            {
                "id": "field-4",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": field4_geometry,
                "properties": {
                    "area": 22.3,
                    "cropType": "Timothy Hay"
                }
            }
        ]
    else:
        # For unknown farm/crop combinations, return empty array
        # In the future, this could generate estimated fields using make_bbox_polygon
        # For now, only show hardcoded sample data:
        # - farm-1 (AB) + crop-1 (Canola) → field-1, field-2
        # - farm-2 (BC) + crop-2 (Timothy Hay) → field-3, field-4
        fields = []
    
    # Ensure all fields have geometry (safety check)
    for field in fields:
        if not field.get("geometry"):
            # Fallback: create estimated polygon from farm anchor
            try:
                lat, lng = get_farm_anchor(farm_id)
                field["geometry"] = make_bbox_polygon(lat, lng, delta_deg=0.005)
            except ValueError:
                # If farm_id is unknown, use farm-1 as default
                lat, lng = get_farm_anchor("farm-1")
                field["geometry"] = make_bbox_polygon(lat, lng, delta_deg=0.005)
    
    return APIResponse(
        data=fields,
        timestamp="2024-01-01T00:00:00Z",
        status="success"
    )


@router.post("/fields/upload")
async def upload_field_boundary(
    farm_id: str,
    crop_id: str,
    file: UploadFile = File(...)
):
    """
    Upload field boundary GeoJSON file
    """
    # TODO: Implement GeoJSON validation and storage
    return {
        "message": "Field boundary uploaded successfully",
        "farmId": farm_id,
        "cropId": crop_id,
        "filename": file.filename
    }

