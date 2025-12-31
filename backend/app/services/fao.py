"""
FAO API service
"""

import httpx
from app.config import settings
from typing import Dict, Any, List, Optional

# Crop name to FAO item code mapping (common crops)
CROP_NAME_TO_FAO_CODE = {
    "tomatoes": "2547",
    "corn": "56",
    "wheat": "15",
    "rice": "27",
    "soybeans": "236",
    "potatoes": "116",
    "barley": "44",
    "sorghum": "83",
    "millet": "79",
    "oats": "75",
}


async def get_crop_metadata(crop_id: str, crop_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get crop metadata from FAO API
    
    Args:
        crop_id: Internal crop ID
        crop_name: Crop name (lowercase) for FAO code lookup
    
    Returns:
        Dictionary with crop metadata from FAO
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Get crop definitions/items from FAO
            response = await client.get(
                f"{settings.fao_api_base_url}/definitions/item"
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract items from response
            items = []
            if isinstance(data, dict):
                items = data.get("data", [])
            elif isinstance(data, list):
                items = data
            
            # Try to find matching crop by name
            matched_item = None
            if crop_name:
                crop_name_lower = crop_name.lower()
                # First try direct mapping
                fao_code = CROP_NAME_TO_FAO_CODE.get(crop_name_lower)
                if fao_code:
                    matched_item = next(
                        (item for item in items if str(item.get("item_code")) == fao_code),
                        None
                    )
                
                # If not found, try fuzzy matching by name
                if not matched_item:
                    matched_item = next(
                        (item for item in items 
                         if crop_name_lower in item.get("item", "").lower()),
                        None
                    )
            
            # Build response
            result = {
                "cropId": crop_id,
                "cropName": crop_name,
                "source": "FAO",
                "matched": matched_item is not None,
            }
            
            if matched_item:
                result["metadata"] = {
                    "itemCode": matched_item.get("item_code"),
                    "itemName": matched_item.get("item"),
                    "itemGroup": matched_item.get("item_group"),
                    "itemGroupCode": matched_item.get("item_group_code"),
                }
            else:
                result["metadata"] = None
                result["availableItems"] = [
                    {
                        "code": item.get("item_code"),
                        "name": item.get("item"),
                    }
                    for item in items[:20]  # Return first 20 items as reference
                ]
            
            return result
            
        except httpx.TimeoutException:
            return {
                "cropId": crop_id,
                "cropName": crop_name,
                "source": "FAO",
                "error": "Request timeout",
                "metadata": None
            }
        except httpx.HTTPStatusError as e:
            return {
                "cropId": crop_id,
                "cropName": crop_name,
                "source": "FAO",
                "error": f"HTTP {e.response.status_code}: {e.response.text[:100]}",
                "metadata": None
            }
        except Exception as e:
            return {
                "cropId": crop_id,
                "cropName": crop_name,
                "source": "FAO",
                "error": str(e),
                "metadata": None
            }

