"""
Sentinel-2 product download service
Downloads Sentinel-2 products and extracts bands for NDVI calculation
"""

from app.services.copernicus_auth import get_authenticated_client
from typing import Optional, Dict, Any
import httpx
import os
import tempfile
import zipfile
import asyncio


async def download_sentinel2_product(
    product_id: str,
    download_url: Optional[str] = None
) -> Optional[str]:
    """
    Download a Sentinel-2 product
    
    Args:
        product_id: Product identifier
        download_url: Optional download URL (if not provided, will construct from product_id)
    
    Returns:
        Path to downloaded product directory or None if download fails
    """
    client = await get_authenticated_client()
    if not client:
        print("[Sentinel2 Download] Authentication failed")
        return None
    
    try:
        # Construct download URL if not provided
        if not download_url:
            download_url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products('{product_id}')/$value"
        
        print(f"[Sentinel2 Download] Downloading product {product_id} from {download_url}")
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp(prefix="sentinel2_")
        zip_path = os.path.join(temp_dir, f"{product_id}.zip")
        
        # Download the product (this is a large file, may take time)
        async with client.stream('GET', download_url) as response:
            if response.status_code != 200:
                print(f"[Sentinel2 Download] Download failed: {response.status_code} - {response.text[:200]}")
                return None
            
            # Stream download to file
            with open(zip_path, 'wb') as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
        
        print(f"[Sentinel2 Download] Downloaded {os.path.getsize(zip_path) / (1024*1024):.2f} MB")
        
        # Extract ZIP file
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Clean up ZIP file
        os.remove(zip_path)
        
        print(f"[Sentinel2 Download] Extracted to {extract_dir}")
        return extract_dir
        
    except Exception as e:
        print(f"[Sentinel2 Download] Error downloading product: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if client:
            await client.aclose()


async def find_band_files(product_dir: str, band: str) -> Optional[str]:
    """
    Find band files in extracted Sentinel-2 product
    
    Args:
        product_dir: Path to extracted product directory
        band: Band identifier (e.g., 'B04' for Red, 'B08' for NIR)
    
    Returns:
        Path to band file or None if not found
    """
    # Sentinel-2 L2A structure: S2A_MSIL2A_YYYYMMDDTHHMMSS_NXXXX_RXXX_TXXYYY_YYYYMMDDTHHMMSS.SAFE/
    # Inside: GRANULE/L2A_TXXYYY_YYYYMMDDTHHMMSS/IMG_DATA/R10m/ or R20m/ or R60m/
    # Band files: TXXYYY_YYYYMMDDTHHMMSS_BXX_10m.jp2
    
    for root, dirs, files in os.walk(product_dir):
        for file in files:
            if file.endswith('.jp2') and f'_{band}_' in file:
                return os.path.join(root, file)
    
    return None


async def get_band_paths(product_dir: str) -> Dict[str, Optional[str]]:
    """
    Get paths to Red (B04) and NIR (B08) band files
    
    Args:
        product_dir: Path to extracted product directory
    
    Returns:
        Dictionary with 'red' and 'nir' band file paths
    """
    red_path = await find_band_files(product_dir, 'B04')
    nir_path = await find_band_files(product_dir, 'B08')
    
    return {
        'red': red_path,
        'nir': nir_path
    }

