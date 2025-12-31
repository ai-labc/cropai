"""
Sentinel-2 data processing service
"""

from app.config import settings
from app.api.models import NDVIGrid, GridData, GridBounds, TimeSeriesData
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

# Try to import eodag for Sentinel-2 data access
try:
    from eodag import EODataAccessGateway
    HAS_EODAG = True
except ImportError:
    HAS_EODAG = False
    print("[Sentinel2] Warning: eodag not installed. Using mock data.")

# Try to import numpy, fallback to random if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


async def calculate_ndvi(
    field_id: str,
    geometry: Dict[str, Any],
    date_start: str,
    date_end: str
) -> NDVIGrid:
    """
    Calculate NDVI for a field polygon and date range
    
    This function:
    1. Authenticates with Copernicus Data Space API
    2. Searches and downloads Sentinel-2 products
    3. Processes bands and calculates NDVI = (NIR - Red) / (NIR + Red)
    4. Applies field polygon mask
    5. Calculates statistics (mean, median) per field
    6. Generates visualization grid
    
    For MVP, returns structured mock data. Real implementation would:
    - Use eodag or sentinelhub to access Copernicus Data Space
    - Download multispectral bands (B04=Red, B08=NIR, B02=Blue)
    - Process with rasterio/geopandas
    - Calculate NDVI and EVI
    """
    # Extract bounds from geometry
    if geometry.get("type") == "Polygon" and geometry.get("coordinates"):
        coords = geometry["coordinates"][0]  # First ring
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        bounds = GridBounds(
            north=max(lats),
            south=min(lats),
            east=max(lngs),
            west=min(lngs)
        )
    else:
        # Default bounds
        bounds = GridBounds(
            north=52.624167,  # Hartland Colony, Alberta
            south=52.614167,
            east=-113.087639,
            west=-113.102639
        )
    
    # Try to use real Copernicus Data Space API if credentials are available
    if settings.copernicus_client_id and settings.copernicus_client_secret:
        try:
            from app.services.sentinel2_search import search_sentinel2_products
            
            # Extract bounding box from geometry
            if geometry.get("type") == "Polygon" and geometry.get("coordinates"):
                coords = geometry["coordinates"][0]  # First ring
                lngs = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                bbox = [min(lngs), min(lats), max(lngs), max(lats)]  # [west, south, east, north]
            else:
                # Default bbox (Hartland Colony, Alberta area)
                bbox = [-113.102639, 52.614167, -113.087639, 52.624167]
            
            # Search for Sentinel-2 products
            products = await search_sentinel2_products(
                bbox=bbox,
                start_date=date_start,
                end_date=date_end,
                cloud_cover_percentage=30.0,  # Max 30% cloud cover
                max_results=5
            )
            
            if products:
                print(f"[Sentinel2] Found {len(products)} products, using most recent for NDVI calculation")
                
                # Use the most recent product (first in list, sorted by date desc)
                most_recent_product = products[0]
                product_id = most_recent_product.get("id", "")
                download_url = most_recent_product.get("link", "")
                
                if product_id and download_url:
                    try:
                        from app.services.sentinel2_download import download_sentinel2_product, get_band_paths
                        from app.services.ndvi_calculator import calculate_ndvi_from_bands
                        
                        # Download the product
                        product_dir = await download_sentinel2_product(product_id, download_url)
                        
                        if product_dir:
                            # Find band files
                            band_paths = await get_band_paths(product_dir)
                            red_path = band_paths.get("red")
                            nir_path = band_paths.get("nir")
                            
                            if red_path and nir_path:
                                # Calculate NDVI
                                ndvi_result = calculate_ndvi_from_bands(
                                    red_path,
                                    nir_path,
                                    field_geometry=geometry
                                )
                                
                                # Clean up downloaded product
                                import shutil
                                try:
                                    shutil.rmtree(product_dir)
                                except:
                                    pass
                                
                                # Return NDVI grid
                                return NDVIGrid(
                                    fieldId=field_id,
                                    timestamp=datetime.now().isoformat(),
                                    grid=GridData(
                                        resolution=ndvi_result.get('resolution', 10.0),
                                        bounds=GridBounds(**ndvi_result.get('bounds', {
                                            'north': 52.624167,  # Hartland Colony, Alberta
                                            'south': 52.614167,
                                            'east': -113.087639,
                                            'west': -113.102639
                                        })),
                                        values=ndvi_result.get('grid', [])
                                    )
                                )
                            else:
                                print(f"[Sentinel2] Could not find band files: Red={red_path}, NIR={nir_path}")
                                # Clean up
                                import shutil
                                try:
                                    shutil.rmtree(product_dir)
                                except:
                                    pass
                        else:
                            print("[Sentinel2] Product download failed, using mock data")
                    except Exception as e:
                        print(f"[Sentinel2] Error processing product: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fall through to mock data
            else:
                print("[Sentinel2] No products found, using mock data")
        except Exception as e:
            print(f"[Sentinel2] Copernicus API search failed: {e}")
            import traceback
            traceback.print_exc()
            # Fall through to mock data
    
    # Generate mock NDVI grid (values between 0.2 and 0.9)
    # Downsample to 64x64 for MVP
    grid_size = 64
    if HAS_NUMPY:
        values = [[0.2 + np.random.random() * 0.7 for _ in range(grid_size)] for _ in range(grid_size)]
    else:
        values = [[0.2 + random.random() * 0.7 for _ in range(grid_size)] for _ in range(grid_size)]
    
    return NDVIGrid(
        fieldId=field_id,
        timestamp=datetime.now().isoformat(),
        grid=GridData(
            resolution=10.0,  # 10 meters per pixel (Sentinel-2 resolution)
            bounds=bounds,
            values=values
        )
    )


async def get_ndvi_timeline(
    field_id: str,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
) -> List[TimeSeriesData]:
    """
    Get NDVI timeline (average/median) for a field
    
    Returns time series of NDVI values calculated from Sentinel-2 data
    """
    # Parse dates
    if date_end:
        end_date = datetime.fromisoformat(date_end.replace('Z', '+00:00'))
    else:
        end_date = datetime.now()
    
    if date_start:
        start_date = datetime.fromisoformat(date_start.replace('Z', '+00:00'))
    else:
        start_date = end_date - timedelta(days=30)
    
    # For MVP: Generate realistic mock timeline
    # Real implementation would:
    # 1. Query Sentinel-2 products for date range
    # 2. Calculate NDVI for each date
    # 3. Average over field polygon
    # 4. Return time series
    
    timeline = []
    current_date = start_date.replace(hour=12, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Generate daily values (Sentinel-2 revisits every 5 days, but we'll show daily for smooth chart)
    base_ndvi = 0.6
    day_count = 0
    
    while current_date <= end_date:
        # Simulate seasonal NDVI variation
        day_of_year = current_date.timetuple().tm_yday
        seasonal_variation = 0.1 * (1 + (day_of_year / 365.0) * 2 - 1)
        
        if HAS_NUMPY:
            ndvi_value = base_ndvi + seasonal_variation + np.random.random() * 0.2 - 0.1
        else:
            ndvi_value = base_ndvi + seasonal_variation + random.random() * 0.2 - 0.1
        
        # Clamp to valid NDVI range
        ndvi_value = max(0.0, min(1.0, ndvi_value))
        
        timeline.append(TimeSeriesData(
            timestamp=current_date.isoformat(),
            value=round(ndvi_value, 3)
        ))
        
        current_date += timedelta(days=1)
        day_count += 1
    
    return timeline

