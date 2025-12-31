"""
Test script to verify Copernicus Data Space API endpoints
"""

import asyncio
import httpx
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.config import settings
from app.services.copernicus_auth import get_access_token, get_authenticated_client


async def test_authentication():
    """Test OAuth2 authentication"""
    print("=" * 60)
    print("Testing Copernicus Data Space Authentication")
    print("=" * 60)
    
    token = await get_access_token()
    if token:
        print(f"✅ Authentication successful")
        print(f"Token (first 30 chars): {token[:30]}...")
        return True
    else:
        print("❌ Authentication failed")
        return False


async def test_odata_endpoint():
    """Test OData API endpoint"""
    print("\n" + "=" * 60)
    print("Testing OData API Endpoint")
    print("=" * 60)
    
    client = await get_authenticated_client()
    if not client:
        print("❌ Cannot get authenticated client")
        return False
    
    # Try different OData endpoints
    endpoints = [
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        "https://dataspace.copernicus.eu/odata/v1/Products",
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$top=1",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            response = await client.get(endpoint, params={"$top": "1", "$format": "json"})
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    print(f"✅ Success! Response keys: {list(data.keys())}")
                else:
                    print(f"✅ Success! Response is a list with {len(data) if hasattr(data, '__len__') else 'unknown'} items")
                print(f"Response preview: {str(data)[:200]}...")
                return True
            else:
                print(f"❌ Failed: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await client.aclose()
    return False


async def test_stac_endpoint():
    """Test STAC API endpoint"""
    print("\n" + "=" * 60)
    print("Testing STAC API Endpoint")
    print("=" * 60)
    
    client = await get_authenticated_client()
    if not client:
        print("❌ Cannot get authenticated client")
        return False
    
    # Try STAC endpoints
    endpoints = [
        "https://dataspace.copernicus.eu/api/v1/stac/collections",
        "https://catalogue.dataspace.copernicus.eu/api/v1/stac/collections",
        "https://dataspace.copernicus.eu/stac/v1/collections",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            response = await client.get(endpoint)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response type: {type(data)}")
                print(f"Response preview: {str(data)[:200]}...")
                return True
            else:
                print(f"❌ Failed: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await client.aclose()
    return False


async def test_catalog_endpoint():
    """Test Catalog API endpoint"""
    print("\n" + "=" * 60)
    print("Testing Catalog API Endpoint")
    print("=" * 60)
    
    client = await get_authenticated_client()
    if not client:
        print("❌ Cannot get authenticated client")
        return False
    
    # Try Catalog endpoints
    endpoints = [
        "https://dataspace.copernicus.eu/api/v1/catalog/1.0.0/search",
        "https://catalogue.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            # STAC search request
            search_request = {
                "collections": ["sentinel-s2-l2a"],
                "bbox": [-122.5, 37.7, -122.3, 37.8],
                "datetime": "2024-12-01T00:00:00Z/2024-12-10T23:59:59Z",
                "limit": 1
            }
            
            response = await client.post(endpoint, json=search_request)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response type: {type(data)}")
                print(f"Response preview: {str(data)[:200]}...")
                return True
            else:
                print(f"❌ Failed: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await client.aclose()
    return False


async def test_product_endpoint():
    """Test Product API endpoint"""
    print("\n" + "=" * 60)
    print("Testing Product API Endpoint")
    print("=" * 60)
    
    client = await get_authenticated_client()
    if not client:
        print("❌ Cannot get authenticated client")
        return False
    
    # Try Product endpoints
    endpoints = [
        "https://dataspace.copernicus.eu/api/v1/products",
        "https://catalogue.dataspace.copernicus.eu/api/v1/products",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            response = await client.get(endpoint, params={"limit": "1"})
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response type: {type(data)}")
                print(f"Response preview: {str(data)[:200]}...")
                return True
            else:
                print(f"❌ Failed: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await client.aclose()
    return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Copernicus Data Space API Endpoint Testing")
    print("=" * 60)
    print(f"Client ID: {settings.copernicus_client_id[:20] if settings.copernicus_client_id else 'NOT SET'}...")
    print(f"Client Secret: {'SET' if settings.copernicus_client_secret else 'NOT SET'}")
    
    # Test authentication first
    auth_success = await test_authentication()
    if not auth_success:
        print("\n❌ Authentication failed. Cannot test other endpoints.")
        return
    
    # Test various endpoints
    results = {
        "OData": await test_odata_endpoint(),
        "STAC": await test_stac_endpoint(),
        "Catalog": await test_catalog_endpoint(),
        "Product": await test_product_endpoint(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for endpoint, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {endpoint} API")
    
    working_endpoints = [name for name, success in results.items() if success]
    if working_endpoints:
        print(f"\n✅ Working endpoints: {', '.join(working_endpoints)}")
    else:
        print("\n❌ No working endpoints found")


if __name__ == "__main__":
    asyncio.run(main())

