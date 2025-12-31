"""
ERA5 weather data service
"""

from app.config import settings
from app.api.models import TimeSeriesData
from typing import List, Optional
from datetime import datetime, timedelta
import random
import os

# Try to import cdsapi
try:
    import cdsapi
    HAS_CDSAPI = True
except ImportError:
    HAS_CDSAPI = False
    print("[ERA5] Warning: cdsapi not installed. Using mock data.")

# Try to import numpy, fallback to random if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def _setup_cds_client():
    """Setup CDS API client"""
    if not HAS_CDSAPI:
        return None
    
    # CDS API requires a config file or environment variables
    # Create config dict from settings
    cds_config = {
        'url': settings.cds_url,
        'key': settings.cds_key,
    }
    
    try:
        client = cdsapi.Client(**cds_config)
        return client
    except Exception as e:
        print(f"[ERA5] Failed to create CDS client: {e}")
        return None


async def get_weather_data(
    lat: float,
    lng: float,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
) -> List[TimeSeriesData]:
    """
    Get weather data from ERA5 for a location
    
    Args:
        lat: Latitude
        lng: Longitude
        date_start: Start date (YYYY-MM-DD), defaults to 30 days ago
        date_end: End date (YYYY-MM-DD), defaults to today
    
    Returns:
        List of TimeSeriesData with temperature values
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
        print(f"[ERA5] Date parsing error: {e}, using defaults")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # Normalize dates to strings for cache lookup
    date_start_str = start_date.strftime('%Y-%m-%d')
    date_end_str = end_date.strftime('%Y-%m-%d')
    
    # Check cache first
    from app.database import get_weather_cache, set_weather_cache
    cached_data = get_weather_cache(lat, lng, date_start_str, date_end_str)
    if cached_data:
        print(f"[ERA5] Cache hit for {lat}, {lng}, {date_start_str} to {date_end_str}")
        # Convert dict back to TimeSeriesData objects
        return [TimeSeriesData(**item) for item in cached_data]
    
    print(f"[ERA5] Cache miss, fetching from API for {lat}, {lng}, {date_start_str} to {date_end_str}")
    
    # For MVP, we'll use mock data but structure it for real API integration
    # Real implementation would:
    # 1. Use cdsapi.Client to request ERA5 data
    # 2. Download NetCDF files to cache
    # 3. Use xarray or netCDF4 to read data
    # 4. Extract data for lat/lng coordinates
    # 5. Return time series
    
    if HAS_CDSAPI and settings.cds_key:
        client = _setup_cds_client()
        if client:
            try:
                # CDS API는 동기식이므로 별도 스레드에서 실행
                # For MVP, we'll use async wrapper or keep mock data
                # Real implementation would:
                # 1. Use asyncio.to_thread() or run_in_executor() for CDS API calls
                # 2. Download NetCDF files
                # 3. Parse with xarray or netCDF4
                # 4. Extract data for lat/lng coordinates
                # 5. Return time series
                
                # CDS API는 동기식이므로 asyncio.to_thread()로 실행
                import asyncio
                import os
                import tempfile
                
                # Create temporary file for download
                temp_dir = settings.cache_dir if hasattr(settings, 'cache_dir') else tempfile.gettempdir()
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, f"era5_{lat}_{lng}_{start_date.date()}.nc")
                
                def sync_cds_call():
                    """Synchronous CDS API call"""
                    try:
                        # Calculate date range for CDS API
                        # CDS API requires year, month, day lists
                        years = []
                        months = []
                        days = []
                        current = start_date
                        while current <= end_date:
                            year = current.year
                            month = current.month
                            day = current.day
                            if year not in years:
                                years.append(str(year))
                            if month not in months:
                                months.append(str(month))
                            if day not in days:
                                days.append(str(day))
                            current += timedelta(days=1)
                        
                        # Request ERA5 data
                        client.retrieve(
                            'reanalysis-era5-single-levels',
                            {
                                'product_type': 'reanalysis',
                                'variable': '2m_temperature',  # Start with temperature
                                'year': years,
                                'month': months,
                                'day': days,
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
                        print(f"[ERA5] CDS API retrieve failed: {e}")
                        return None
                
                # Run CDS API call in thread pool
                downloaded_file = await asyncio.to_thread(sync_cds_call)
                
                if downloaded_file and os.path.exists(downloaded_file):
                    print(f"[ERA5] Downloaded ERA5 data to {downloaded_file}")
                    
                    # Try to parse NetCDF file
                    try:
                        # Try importing xarray first (preferred)
                        try:
                            import xarray as xr
                            HAS_XARRAY = True
                        except ImportError:
                            HAS_XARRAY = False
                            try:
                                import netCDF4
                                HAS_NETCDF4 = True
                            except ImportError:
                                HAS_NETCDF4 = False
                        
                        if HAS_XARRAY:
                            # Parse with xarray
                            ds = xr.open_dataset(downloaded_file)
                            
                            # Extract temperature data for specific lat/lng
                            temp_data = ds['t2m']  # 2m temperature variable
                            
                            # Select nearest point for each time step
                            # xarray sel() returns a DataArray with time dimension
                            point_data = temp_data.sel(
                                latitude=lat,
                                longitude=lng,
                                method='nearest'
                            )
                            
                            # Convert to time series
                            timeline = []
                            # point_data is already selected for lat/lng, now iterate over time
                            # Check dimensions of point_data
                            if 'time' in point_data.dims:
                                # Iterate over time dimension
                                time_coords = point_data.time.values
                                temp_values = point_data.values
                                
                                for time_idx in range(len(time_coords)):
                                    time_coord = time_coords[time_idx]
                                    # Get temperature value (handle numpy array)
                                    if hasattr(temp_values, '__len__') and not isinstance(temp_values, str):
                                        temp_value = float(temp_values[time_idx])
                                    else:
                                        temp_value = float(temp_values)
                                    
                                    # Convert from Kelvin to Celsius
                                    temp_celsius = temp_value - 273.15
                                    
                                    # Convert numpy datetime64 to ISO string
                                    if hasattr(time_coord, 'item'):
                                        dt = time_coord.item()
                                    else:
                                        dt = time_coord
                                    
                                    # Convert to ISO string
                                    if isinstance(dt, str):
                                        timestamp = dt
                                    elif hasattr(dt, 'isoformat'):
                                        timestamp = dt.isoformat()
                                    else:
                                        # Convert pandas Timestamp or numpy datetime64
                                        import pandas as pd
                                        if isinstance(dt, pd.Timestamp):
                                            timestamp = dt.isoformat()
                                        else:
                                            # numpy datetime64 - convert to string then parse
                                            timestamp = str(dt)
                                    
                                    timeline.append(TimeSeriesData(
                                        timestamp=timestamp,
                                        value=round(temp_celsius, 2)
                                    ))
                            else:
                                # Single value (no time dimension) - convert to scalar
                                try:
                                    if hasattr(point_data.values, 'item'):
                                        temp_value = float(point_data.values.item())
                                    elif hasattr(point_data.values, '__len__') and len(point_data.values) == 1:
                                        temp_value = float(point_data.values[0])
                                    else:
                                        temp_value = float(point_data.values)
                                except:
                                    # Fallback: use first value if array
                                    temp_value = float(point_data.values.flatten()[0])
                                
                                temp_celsius = temp_value - 273.15
                                # Use current time or data time
                                timeline.append(TimeSeriesData(
                                    timestamp=datetime.now().isoformat(),
                                    value=round(temp_celsius, 2)
                                ))
                            
                            ds.close()
                            
                            # Clean up temp file
                            try:
                                os.remove(downloaded_file)
                            except:
                                pass
                            
                            if timeline:
                                print(f"[ERA5] Successfully extracted {len(timeline)} data points from ERA5")
                                return timeline
                            else:
                                print(f"[ERA5] No data extracted, using mock data")
                        elif HAS_NETCDF4:
                            # Parse with netCDF4 (fallback)
                            nc = netCDF4.Dataset(downloaded_file, 'r')
                            # Extract data (implementation similar to xarray)
                            nc.close()
                            print(f"[ERA5] netCDF4 parsing not fully implemented, using mock data")
                        else:
                            print(f"[ERA5] No NetCDF library available (xarray/netCDF4), using mock data")
                    except Exception as e:
                        print(f"[ERA5] Error parsing NetCDF file: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fall through to mock data
                else:
                    print(f"[ERA5] CDS API download failed, using mock data")
                
            except Exception as e:
                print(f"[ERA5] CDS API setup failed: {e}")
                # Fall through to mock data
    
    # Generate mock time series data
    timeline = []
    current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    while current_date <= end_date:
        # Generate realistic temperature values (varies by day)
        day_of_year = current_date.timetuple().tm_yday
        # Simple seasonal variation (sine wave approximation)
        seasonal_factor = (day_of_year / 365.0) * 2 * 3.14159  # Convert to radians
        base_temp = 15 + 10 * (1 + (seasonal_factor - 1.57) / 1.57)  # Rough seasonal cycle
        
        if HAS_NUMPY:
            temp = base_temp + np.random.random() * 10 - 5
        else:
            temp = base_temp + random.random() * 10 - 5
        
        timeline.append(TimeSeriesData(
            timestamp=current_date.isoformat(),
            value=round(temp, 2)
        ))
        
        current_date += timedelta(days=1)
    
    # Cache mock data too (for consistency)
    set_weather_cache(lat, lng, date_start_str, date_end_str, timeline)
    
    return timeline

