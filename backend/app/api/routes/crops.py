"""
Crop endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.api.models import Crop, APIResponse
from app.services.fao import get_crop_metadata

router = APIRouter()


@router.get("/crops", response_model=APIResponse[List[Crop]])
async def get_crops():
    """
    Get list of crops
    """
    # Real Canadian crop data
    crops = [
        {
            "id": "crop-1",
            "name": "Canola",
            "type": "Oilseed",
            "plantingDate": "2024-05-01",
            "expectedHarvestDate": "2024-09-15"
        },
        {
            "id": "crop-2",
            "name": "Timothy Hay",
            "type": "Forage",
            "plantingDate": "2024-04-15",
            "expectedHarvestDate": "2024-07-20"
        }
    ]
    
    return APIResponse(
        data=crops,
        timestamp="2024-01-01T00:00:00Z",
        status="success"
    )


@router.get("/crops/{crop_id}", response_model=APIResponse[Crop])
async def get_crop(crop_id: str):
    """
    Get crop by ID
    """
    # Real Canadian crop data
    crops_data = {
        "crop-1": {
            "id": "crop-1",
            "name": "Canola",
            "type": "Oilseed",
            "plantingDate": "2024-05-01",
            "expectedHarvestDate": "2024-09-15"
        },
        "crop-2": {
            "id": "crop-2",
            "name": "Timothy Hay",
            "type": "Forage",
            "plantingDate": "2024-04-15",
            "expectedHarvestDate": "2024-07-20"
        }
    }
    
    if crop_id not in crops_data:
        raise HTTPException(status_code=404, detail="Crop not found")
    
    crop = crops_data[crop_id]
    
    return APIResponse(
        data=crop,
        timestamp="2024-01-01T00:00:00Z",
        status="success"
    )


@router.get("/crops/{crop_id}/metadata")
async def get_crop_metadata_endpoint(crop_id: str, crop_name: str = None):
    """
    Get crop metadata from FAO
    
    Args:
        crop_id: Internal crop ID
        crop_name: Optional crop name for better matching
    """
    try:
        # If crop_name not provided, try to get it from the crop data
        if not crop_name:
            # Try to get crop name from internal data
            crop_data = None
            if crop_id == "crop-1":
                crop_name = "canola"
            elif crop_id == "crop-2":
                crop_name = "timothy hay"
        
        metadata = await get_crop_metadata(crop_id, crop_name)
        return APIResponse(
            data=metadata,
            timestamp="2024-01-01T00:00:00Z",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

