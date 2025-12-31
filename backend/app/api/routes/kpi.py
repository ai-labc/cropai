"""
KPI Summary endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from app.api.models import KPISummary, APIResponse
from app.services.kpi_calculator import calculate_kpi_summary
from app.services.precompute import get_precomputed_data, precompute_kpi
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/kpi", response_model=APIResponse[KPISummary])
async def get_kpi_summary(
    farm_id: Optional[str] = Query(None, description="Farm ID"),
    crop_id: Optional[str] = Query(None, description="Crop ID"),
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    field_id: Optional[str] = Query(None, description="Field ID")
):
    """
    Get KPI summary (productivity, water efficiency, ESG accuracy)
    Uses precomputed JSON if available, otherwise computes on-demand
    """
    try:
        # Try to get precomputed data first
        key_parts = []
        if farm_id:
            key_parts.append(farm_id)
        if crop_id:
            key_parts.append(crop_id)
        if field_id:
            key_parts.append(field_id)
        if lat and lng:
            key_parts.append(f"{lat:.4f}_{lng:.4f}")
        
        key = "_".join(key_parts) if key_parts else "default"
        
        precomputed = get_precomputed_data("kpi", key)
        
        if precomputed and precomputed.get("data"):
            # Return precomputed data
            return APIResponse(
                data=precomputed["data"],
                timestamp=precomputed.get("computed_at", datetime.now().isoformat()),
                status="success"
            )
        
        # Fallback to on-demand calculation
        kpi_data = await calculate_kpi_summary(
            farm_id=farm_id,
            crop_id=crop_id,
            field_id=field_id,
            lat=lat,
            lng=lng
        )
        
        # Optionally trigger background precomputation for next time
        # (don't await to avoid blocking response)
        try:
            import asyncio
            asyncio.create_task(precompute_kpi(farm_id, crop_id, field_id, lat, lng))
        except:
            pass  # Silently fail background precomputation
        
        return APIResponse(
            data=kpi_data,
            timestamp=datetime.now().isoformat(),
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

