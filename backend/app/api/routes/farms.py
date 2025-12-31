"""
Farm endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.api.models import Farm, APIResponse

router = APIRouter()


@router.get("/farms", response_model=APIResponse[List[Farm]])
async def get_farms():
    """
    Get list of farms
    For now, returns mock data. Will be replaced with database query.
    """
    # Real Canadian farm data
    farms = [
        {
            "id": "farm-1",
            "name": "Hartland Colony",
            "location": {"lat": 52.619167, "lng": -113.092639},  # 52°37'09.0"N, 113°05'33.5"W
            "area": 250.5
        },
        {
            "id": "farm-2",
            "name": "Exceedagro Reference Field",
            "location": {"lat": 54.0167, "lng": -124.0167},  # Vanderhoof, BC
            "area": 180.3
        }
    ]
    
    return APIResponse(
        data=farms,
        timestamp="2024-01-01T00:00:00Z",
        status="success"
    )


@router.get("/farms/{farm_id}", response_model=APIResponse[Farm])
async def get_farm(farm_id: str):
    """
    Get farm by ID
    """
    # Real Canadian farm data
    farms_data = {
        "farm-1": {
            "id": "farm-1",
            "name": "Hartland Colony",
            "location": {"lat": 52.619167, "lng": -113.092639},
            "area": 250.5
        },
        "farm-2": {
            "id": "farm-2",
            "name": "Exceedagro Reference Field",
            "location": {"lat": 54.0167, "lng": -124.0167},
            "area": 180.3
        }
    }
    
    if farm_id not in farms_data:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    farm = farms_data[farm_id]
    
    return APIResponse(
        data=farm,
        timestamp="2024-01-01T00:00:00Z",
        status="success"
    )

