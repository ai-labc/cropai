"""
Pydantic models for API requests/responses
These should match the TypeScript types in the frontend
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal, Generic, TypeVar

T = TypeVar('T')


# Farm and Crop models
class Location(BaseModel):
    lat: float
    lng: float


class Farm(BaseModel):
    id: str
    name: str
    location: Location
    area: float  # hectares


class Crop(BaseModel):
    id: str
    name: str
    type: str
    plantingDate: str
    expectedHarvestDate: str


# Field boundary model
class FieldBoundaryProperties(BaseModel):
    area: float
    cropType: str


class FieldBoundary(BaseModel):
    id: str
    farmId: str
    cropId: str
    geometry: Dict[str, Any]  # GeoJSON geometry
    properties: FieldBoundaryProperties


# KPI Summary
class KPISummary(BaseModel):
    productivityIncrease: float  # percentage
    waterEfficiency: float  # percentage
    esgAccuracy: float  # percentage (0-100)
    timestamp: str


# NDVI Grid
class GridBounds(BaseModel):
    north: float
    south: float
    east: float
    west: float


class GridData(BaseModel):
    resolution: float  # meters per pixel
    bounds: GridBounds
    values: List[List[float]]  # 2D array (64x64 for MVP)


class NDVIGrid(BaseModel):
    fieldId: str
    timestamp: str
    grid: GridData


# Stress Index
class StressIndex(BaseModel):
    fieldId: str
    timestamp: str
    grid: GridData


# Time series data
class TimeSeriesData(BaseModel):
    timestamp: str
    value: float


class SoilMoistureData(TimeSeriesData):
    fieldId: str
    depth: Optional[float] = None  # cm


class YieldPredictionData(TimeSeriesData):
    fieldId: str
    confidence: Optional[float] = None  # 0-1


class CarbonMetricsData(TimeSeriesData):
    fieldId: str
    metricType: Literal["sequestration", "emission", "net"]


# API Response wrapper
class APIResponse(BaseModel, Generic[T]):
    data: T
    timestamp: str
    status: Literal["success", "error"]
    message: Optional[str] = None

