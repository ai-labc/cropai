"""
Shared geometry utility service
Provides consistent field geometry generation and farm anchor point lookup
"""

from typing import Dict, Any, Tuple, Optional


def get_farm_anchor(farm_id: str) -> Tuple[float, float]:
    """
    Get the anchor point (lat, lng) for a farm
    
    Args:
        farm_id: Farm ID (e.g., "farm-1", "farm-2")
    
    Returns:
        Tuple of (lat, lng) in degrees
    
    Raises:
        ValueError: If farm_id is not recognized
    """
    farm_anchors = {
        "farm-1": (52.619167, -113.092639),  # Hartland Colony, Alberta
        "farm-2": (54.0167, -124.0167),      # Exceedagro Reference Field, BC
    }
    
    if farm_id not in farm_anchors:
        raise ValueError(f"Unknown farm_id: {farm_id}")
    
    lat, lng = farm_anchors[farm_id]
    return lat, lng


def make_bbox_polygon(lat: float, lng: float, delta_deg: float = 0.005) -> Dict[str, Any]:
    """
    Create a square bounding box polygon from a center point
    
    Args:
        lat: Center latitude in degrees
        lng: Center longitude in degrees
        delta_deg: Half-width of the square in degrees (default 0.005 ≈ ~500m)
    
    Returns:
        GeoJSON Polygon geometry dict
    
    Note:
        Coordinates are in [lng, lat] format (GeoJSON standard)
        Polygon is closed (first point == last point)
    """
    return {
        "type": "Polygon",
        "coordinates": [[
            [lng - delta_deg, lat - delta_deg],  # SW
            [lng + delta_deg, lat - delta_deg],  # SE
            [lng + delta_deg, lat + delta_deg],  # NE
            [lng - delta_deg, lat + delta_deg],  # NW
            [lng - delta_deg, lat - delta_deg]   # Close polygon
        ]]
    }


def get_field_geometry_by_id(field_id: str) -> Optional[Dict[str, Any]]:
    """
    Get field geometry by field_id
    This is the single source of truth for field geometry
    
    Args:
        field_id: Field ID (e.g., "field-1", "field-2")
    
    Returns:
        GeoJSON geometry dict or None if not found
    """
    # Field data mapping (same structure as fields.py)
    # This should match the data in fields.py exactly
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
        return field_data_map[field_id]["geometry"]
    
    return None


def get_field_geometry_with_fallback(field_id: str) -> Dict[str, Any]:
    """
    Get field geometry by field_id with fallback to estimated polygon based on farm location
    
    Args:
        field_id: Field ID (e.g., "field-1", "field-2")
    
    Returns:
        GeoJSON geometry dict (always returns a geometry, never None)
    
    Raises:
        ValueError: If field_id cannot be parsed to extract farm_id
    """
    # First, try to get exact geometry
    geometry = get_field_geometry_by_id(field_id)
    if geometry:
        return geometry
    
    # Fallback: extract farm_id from field_id and create estimated polygon
    import re
    farm_match = re.search(r'farm-(\d+)', field_id)
    
    if farm_match:
        farm_num = farm_match.group(1)
        farm_id = f"farm-{farm_num}"
        
        try:
            lat, lng = get_farm_anchor(farm_id)
            return make_bbox_polygon(lat, lng, delta_deg=0.005)
        except ValueError:
            # If farm_id is not recognized, default to farm-1
            lat, lng = get_farm_anchor("farm-1")
            return make_bbox_polygon(lat, lng, delta_deg=0.005)
    else:
        # If we can't extract farm_id, default to farm-1 location
        lat, lng = get_farm_anchor("farm-1")
        return make_bbox_polygon(lat, lng, delta_deg=0.005)

