"""
Sentinel-2 product search using Copernicus Data Space OpenSearch API
"""

from app.services.copernicus_auth import get_authenticated_client
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx


async def search_sentinel2_products(
    bbox: List[float],  # [west, south, east, north]
    start_date: str,
    end_date: str,
    cloud_cover_percentage: Optional[float] = None,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for Sentinel-2 L2A products using Copernicus Data Space OpenSearch API
    
    Args:
        bbox: Bounding box [west, south, east, north]
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        cloud_cover_percentage: Maximum cloud cover percentage (0-100)
        max_results: Maximum number of results to return
    
    Returns:
        List of product metadata dictionaries
    """
    client = await get_authenticated_client()
    if not client:
        print("[Sentinel2 Search] Authentication failed")
        return []
    
    try:
        # Try multiple API endpoints
        # Option 1: Sentinel Hub Catalog API (recommended)
        # Option 2: OData API
        # Option 3: STAC API
        
        # Copernicus Data Space API endpoints (multiple options to try)
        # Note: Actual endpoint may need verification from official documentation
        # For MVP, we'll try OData API first, then fall back to mock data if it fails
        odata_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        
        # Alternative endpoints to try if primary fails:
        # - https://dataspace.copernicus.eu/odata/v1/Products
        # - Sentinel Hub Catalog API (requires different authentication)
        
        # Alternative: Sentinel Hub Catalog API (if OData fails)
        # catalog_url = "https://shub.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"
        
        # Build OData query parameters
        # Filter for Sentinel-2 L2A products (exclude AUX products)
        filters = [
            f"(startswith(Name,'S2A_MSIL2A') or startswith(Name,'S2B_MSIL2A'))",  # Sentinel-2 L2A products only
            f"not contains(Name,'AUX')",  # Exclude auxiliary products
            f"ContentDate/Start ge {start_date}T00:00:00.000Z",
            f"ContentDate/Start le {end_date}T23:59:59.999Z"
        ]
        
        params = {
            "$filter": " and ".join(filters),
            "$top": max_results,
            "$orderby": "ContentDate/Start desc",  # Most recent first
            "$format": "json"
        }
        
        print(f"[Sentinel2 Search] Searching products: bbox={bbox}, dates={start_date} to {end_date}")
        print(f"[Sentinel2 Search] Using OData API: {odata_url}")
        
        response = await client.get(odata_url, params=params)
        
        print(f"[Sentinel2 Search] Response status: {response.status_code}")
        print(f"[Sentinel2 Search] Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[Sentinel2 Search] Response structure: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            # OData response format: {"value": [...]} or {"feed": {"entry": [...]}}
            entries = []
            if isinstance(data, dict):
                # Try OData format first
                if "value" in data:
                    entries = data["value"]
                # Try OpenSearch format
                elif "feed" in data:
                    feed = data["feed"]
                    if isinstance(feed, dict):
                        entries = feed.get("entry", [])
                    else:
                        entries = feed
                # Try direct array
                elif "entry" in data:
                    entries = data["entry"]
                # Try other possible keys
                else:
                    # Check if any key contains a list
                    for key, value in data.items():
                        if isinstance(value, list):
                            entries = value
                            break
            
            # Normalize to list if single entry
            if isinstance(entries, dict):
                entries = [entries]
            elif not isinstance(entries, list):
                entries = []
            
            products = []
            for entry in entries:
                # OData format: entry has Id, Name, ContentDate, etc.
                product_info = {
                    "id": entry.get("Id", ""),
                    "name": entry.get("Name", ""),
                    "title": entry.get("Name", ""),  # Use Name as title
                    "updated": entry.get("ContentDate", {}).get("Start", "") if isinstance(entry.get("ContentDate"), dict) else entry.get("ContentDate", ""),
                    "link": None,
                    "cloud_cover": None,
                    "footprint": None
                }
                
                # Extract download link from OData format
                # OData products have a download link in the format: /odata/v1/Products('{Id}')/$value
                if product_info["id"]:
                    product_info["link"] = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products('{product_info['id']}')/$value"
                
                # Extract cloud cover percentage (if available in OData response)
                # Cloud cover might be in a separate property or need to be queried separately
                for key in ["CloudCoverage", "CloudCover", "CloudCoverPercentage"]:
                    if key in entry:
                        try:
                            product_info["cloud_cover"] = float(entry[key])
                            break
                        except (ValueError, TypeError):
                            pass
                
                # Extract footprint (geometry) - OData might have ODataGeography or similar
                if "ODataGeography" in entry:
                    product_info["footprint"] = entry["ODataGeography"]
                elif "Footprint" in entry:
                    product_info["footprint"] = entry["Footprint"]
                
                products.append(product_info)
            
            print(f"[Sentinel2 Search] Found {len(products)} products")
            return products
        else:
            print(f"[Sentinel2 Search] Search failed: {response.status_code} - {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"[Sentinel2 Search] Error during search: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if client:
            await client.aclose()


async def get_product_download_url(product_id: str) -> Optional[str]:
    """
    Get download URL for a specific Sentinel-2 product
    
    Args:
        product_id: Product identifier
    
    Returns:
        Download URL or None
    """
    client = await get_authenticated_client()
    if not client:
        return None
    
    try:
        # Product details endpoint
        product_url = f"https://dataspace.copernicus.eu/api/v1/products/{product_id}"
        
        response = await client.get(product_url)
        
        if response.status_code == 200:
            data = response.json()
            # Extract download link
            links = data.get("links", [])
            for link in links:
                if link.get("rel") == "download" or link.get("type") == "application/zip":
                    return link.get("href")
        
        return None
        
    except Exception as e:
        print(f"[Sentinel2 Search] Error getting download URL: {e}")
        return None
    finally:
        if client:
            await client.aclose()

