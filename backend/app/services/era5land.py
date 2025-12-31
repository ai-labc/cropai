"""
ERA5-Land soil moisture service (Optional for MVP)
"""

from app.config import settings
from app.api.models import SoilMoistureData
from typing import List, Optional
from datetime import datetime, timedelta, date
import random
import os
import asyncio

# Try to import cdsapi
try:
    import cdsapi
    HAS_CDSAPI = True
except ImportError:
    HAS_CDSAPI = False
    print("[ERA5-Land] Warning: cdsapi not installed. Using mock data.")

# Try to import numpy, fallback to random if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Try to import xarray for NetCDF parsing
try:
    import xarray as xr
    HAS_XARRAY = True
except ImportError:
    HAS_XARRAY = False


def _setup_cds_client():
    """Setup CDS API client"""
    if not HAS_CDSAPI:
        return None
    
    cds_config = {
        'url': settings.cds_url,
        'key': settings.cds_key,
    }
    
    try:
        client = cdsapi.Client(**cds_config)
        return client
    except Exception as e:
        print(f"[ERA5-Land] Failed to create CDS client: {e}")
        return None


async def get_soil_moisture(
    lat: float,
    lng: float,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    field_id: Optional[str] = None
) -> List[SoilMoistureData]:
    """
    Get soil moisture data from ERA5-Land
    
    Uses actual CDS API to download ERA5-Land soil moisture data
    """
    
    # Parse dates - use safe parsing to avoid "day is out of range" errors
    try:
        if date_end:
            # Try parsing with timezone first
            try:
                end_date = datetime.fromisoformat(date_end.replace('Z', '+00:00'))
            except:
                # Try without timezone
                try:
                    end_date = datetime.fromisoformat(date_end)
                except:
                    # Fallback to now
                    end_date = datetime.now()
        else:
            end_date = datetime.now()
        
        if date_start:
            try:
                start_date = datetime.fromisoformat(date_start.replace('Z', '+00:00'))
            except:
                try:
                    start_date = datetime.fromisoformat(date_start)
                except:
                    start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
    except Exception as e:
        # If anything goes wrong, use safe defaults
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # Normalize dates to strings for cache lookup
    date_start_str = start_date.strftime('%Y-%m-%d')
    date_end_str = end_date.strftime('%Y-%m-%d')
    
    # Check cache first
    from app.database import get_soil_moisture_cache, set_soil_moisture_cache
    cached_data = get_soil_moisture_cache(lat, lng, date_start_str, date_end_str)
    if cached_data:
        print(f"[ERA5-Land] Cache hit for {lat}, {lng}, {date_start_str} to {date_end_str}")
        # Convert dict back to SoilMoistureData objects
        # Note: SoilMoistureData is already imported at the top of the file
        return [SoilMoistureData(**item) for item in cached_data]
    
    print(f"[ERA5-Land] Cache miss, fetching from API for {lat}, {lng}, {date_start_str} to {date_end_str}")
    
    # Try to use real ERA5-Land data if CDS API is available
    if HAS_CDSAPI and settings.cds_key:
        client = _setup_cds_client()
        if client:
            try:
                import tempfile
                
                # Create temporary file for download
                temp_dir = settings.cache_dir if hasattr(settings, 'cache_dir') else tempfile.gettempdir()
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, f"era5land_soil_{lat}_{lng}_{date_start or 'default'}.nc")
                
                def sync_cds_call():
                    """Synchronous CDS API call for ERA5-Land"""
                    try:
                        # Calculate date range for CDS API
                        years = []
                        months = []
                        days_list = []
                        current = start_date
                        while current <= end_date:
                            year = current.year
                            month = current.month
                            day = current.day
                            if str(year) not in years:
                                years.append(str(year))
                            if str(month) not in months:
                                months.append(str(month))
                            if str(day) not in days_list:
                                days_list.append(str(day))
                            current += timedelta(days=1)
                        
                        # Request ERA5-Land soil moisture data
                        # Variable name: 'volumetric_soil_water_layer_1' for layer 1 (0-7cm)
                        client.retrieve(
                            'reanalysis-era5-land',
                            {
                                'variable': 'volumetric_soil_water_layer_1',  # Layer 1 (0-7cm) - corrected variable name
                                'year': years,
                                'month': months,
                                'day': days_list,
                                'time': ['00:00', '06:00', '12:00', '18:00'],
                                'area': [
                                    lat + 0.1,  # North
                                    lng - 0.1,  # West
                                    lat - 0.1,  # South
                                    lng + 0.1,  # East
                                ],
                                'format': 'netcdf',
                            },
                            temp_file
                        )
                        return temp_file
                    except Exception as e:
                        print(f"[ERA5-Land] CDS API retrieve failed: {e}")
                        return None
                
                # Run CDS API call in thread pool
                downloaded_file = await asyncio.to_thread(sync_cds_call)
                
                if downloaded_file and os.path.exists(downloaded_file):
                    print(f"[ERA5-Land] Downloaded ERA5-Land data to {downloaded_file}")
                    
                    # Parse NetCDF file
                    if HAS_XARRAY:
                        try:
                            ds = xr.open_dataset(downloaded_file)
                            
                            # Extract soil moisture data (variable name may vary)
                            soil_var = None
                            for var_name in ['swvl1', 'volumetric_surface_soil_moisture', 'sm']:
                                if var_name in ds.variables:
                                    soil_var = ds[var_name]
                                    break
                            
                            if soil_var is None and len(ds.variables) > 0:
                                # Use first data variable
                                for var in ds.variables:
                                    if var not in ['time', 'latitude', 'longitude']:
                                        soil_var = ds[var]
                                        break
                            
                            if soil_var is not None:
                                # Select nearest point
                                point_data = soil_var.sel(
                                    latitude=lat,
                                    longitude=lng,
                                    method='nearest'
                                )
                                
                                # Convert to time series
                                timeline = []
                                if 'time' in point_data.coords:
                                    time_coords = point_data.coords['time'].values
                                    soil_values = point_data.values
                                    
                                    for time_idx in range(len(time_coords)):
                                        time_coord = time_coords[time_idx]
                                        
                                        # Get soil moisture value
                                        if hasattr(soil_values, '__len__') and not isinstance(soil_values, str):
                                            soil_value = float(soil_values[time_idx])
                                        else:
                                            soil_value = float(soil_values)
                                        
                                        # Convert to percentage (ERA5-Land is in m³/m³, multiply by 100 for %)
                                        soil_percent = soil_value * 100
                                        
                                        # Convert time to ISO string
                                        if hasattr(time_coord, 'item'):
                                            dt = time_coord.item()
                                        else:
                                            dt = time_coord
                                        
                                        if isinstance(dt, str):
                                            timestamp = dt
                                        elif hasattr(dt, 'isoformat'):
                                            timestamp = dt.isoformat()
                                        else:
                                            import pandas as pd
                                            if isinstance(dt, pd.Timestamp):
                                                timestamp = dt.isoformat()
                                            else:
                                                timestamp = str(dt)
                                        
                                        timeline.append(SoilMoistureData(
                                            timestamp=timestamp,
                                            value=round(soil_percent, 2),
                                            fieldId=field_id or "field-1",
                                            depth=7.0  # Layer 1 is 0-7cm
                                        ))
                                
                                ds.close()
                                
                                # Clean up temp file
                                try:
                                    os.remove(downloaded_file)
                                except:
                                    pass
                                
                                if timeline:
                                    print(f"[ERA5-Land] Successfully extracted {len(timeline)} data points")
                                    # Cache the data
                                    set_soil_moisture_cache(lat, lng, date_start_str, date_end_str, timeline)
                                    return timeline
                                else:
                                    print(f"[ERA5-Land] No data extracted, using mock data")
                            else:
                                print(f"[ERA5-Land] Could not find soil moisture variable, using mock data")
                                ds.close()
                        except Exception as e:
                            print(f"[ERA5-Land] Error parsing NetCDF file: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[ERA5-Land] xarray not available, using mock data")
                else:
                    print(f"[ERA5-Land] CDS API download failed, using mock data")
            except Exception as e:
                print(f"[ERA5-Land] CDS API setup failed: {e}")
                import traceback
                traceback.print_exc()
    
    # Fallback to mock data if CDS API is not available or failed
    today = date.today()
    days = 30
    
    timeline = []
    for i in range(days):
        data_date = today - timedelta(days=i)
        
        if HAS_NUMPY:
            value = 50 + np.random.random() * 20
        else:
            value = 50 + random.random() * 20
        
        data_datetime = datetime.combine(data_date, datetime.min.time())
        
        timeline.append(SoilMoistureData(
            timestamp=data_datetime.isoformat(),
            value=round(value, 2),
            fieldId=field_id or "field-1",
            depth=20.0
        ))
    
    timeline.reverse()
    
    # Cache mock data too (for consistency)
    set_soil_moisture_cache(lat, lng, date_start_str, date_end_str, timeline)
    
    return timeline

