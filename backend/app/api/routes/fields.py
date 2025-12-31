"""
Field boundary endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from app.api.models import FieldBoundary, APIResponse

router = APIRouter()


@router.get("/fields", response_model=APIResponse[List[FieldBoundary]])
async def get_fields(farm_id: str, crop_id: str):
    """
    Get field boundaries for a farm and crop
    """
    # Real field data based on farm and crop
    # Farm 1: Hartland Colony (Alberta) - Canola
    # Farm 2: Exceedagro Reference Field (BC) - Timothy Hay
    
    fields = []
    
    if farm_id == "farm-1" and crop_id == "crop-1":
        # Hartland Colony - Canola fields
        fields = [
            {
                "id": "field-1",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-113.097639, 52.614167],  # SW
                        [-113.087639, 52.614167],  # SE
                        [-113.087639, 52.624167],  # NE
                        [-113.097639, 52.624167],  # NW
                        [-113.097639, 52.614167]   # Close polygon
                    ]]
                },
                "properties": {
                    "area": 25.5,
                    "cropType": "Canola"
                }
            },
            {
                "id": "field-2",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-113.102639, 52.614167],
                        [-113.092639, 52.614167],
                        [-113.092639, 52.624167],
                        [-113.102639, 52.624167],
                        [-113.102639, 52.614167]
                    ]]
                },
                "properties": {
                    "area": 30.2,
                    "cropType": "Canola"
                }
            }
        ]
    elif farm_id == "farm-2" and crop_id == "crop-2":
        # Exceedagro Reference Field - Timothy Hay fields
        fields = [
            {
                "id": "field-3",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-124.02167, 54.01167],  # SW
                        [-124.01167, 54.01167],  # SE
                        [-124.01167, 54.02167],  # NE
                        [-124.02167, 54.02167],  # NW
                        [-124.02167, 54.01167]   # Close polygon
                    ]]
                },
                "properties": {
                    "area": 18.7,
                    "cropType": "Timothy Hay"
                }
            },
            {
                "id": "field-4",
                "farmId": farm_id,
                "cropId": crop_id,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-124.02667, 54.01167],
                        [-124.01667, 54.01167],
                        [-124.01667, 54.02167],
                        [-124.02667, 54.02167],
                        [-124.02667, 54.01167]
                    ]]
                },
                "properties": {
                    "area": 22.3,
                    "cropType": "Timothy Hay"
                }
            }
        ]
    else:
        # Invalid farm/crop combinations - return empty array
        # Only show hardcoded sample data:
        # - farm-1 (AB) + crop-1 (Canola) → field-1, field-2
        # - farm-2 (BC) + crop-2 (Timothy Hay) → field-3, field-4
        # All other combinations return empty array
        fields = []
    
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

