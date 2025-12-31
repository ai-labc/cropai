"""
Database module for caching API responses
Uses SQLite for fast local caching
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.config import settings
import os

# Database file path
DB_PATH = os.path.join(settings.cache_dir, "cache.db")
CACHE_TTL_HOURS = 7 * 24  # Cache data for 7 days (longer cache for better performance)


def get_db_connection():
    """Get SQLite database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Weather data cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            date_start TEXT NOT NULL,
            date_end TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lat, lng, date_start, date_end)
        )
    """)
    
    # Soil moisture cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS soil_moisture_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            date_start TEXT NOT NULL,
            date_end TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lat, lng, date_start, date_end)
        )
    """)
    
    # NDVI cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ndvi_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id TEXT NOT NULL,
            date_start TEXT NOT NULL,
            date_end TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(field_id, date_start, date_end)
        )
    """)
    
    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_lookup ON weather_cache(lat, lng, date_start, date_end)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_soil_lookup ON soil_moisture_cache(lat, lng, date_start, date_end)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ndvi_lookup ON ndvi_cache(field_id, date_start, date_end)")
    
    conn.commit()
    conn.close()


def is_cache_valid(created_at: str) -> bool:
    """Check if cache entry is still valid (within TTL)"""
    try:
        cache_time = datetime.fromisoformat(created_at)
        age = datetime.now() - cache_time
        return age < timedelta(hours=CACHE_TTL_HOURS)
    except:
        return False


def get_weather_cache(lat: float, lng: float, date_start: str, date_end: str) -> Optional[List[Dict[str, Any]]]:
    """Get cached weather data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT data, created_at FROM weather_cache
        WHERE lat = ? AND lng = ? AND date_start = ? AND date_end = ?
    """, (lat, lng, date_start, date_end))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and is_cache_valid(row['created_at']):
        return json.loads(row['data'])
    return None


def set_weather_cache(lat: float, lng: float, date_start: str, date_end: str, data: List[Dict[str, Any]]):
    """Cache weather data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data_json = json.dumps([d.dict() if hasattr(d, 'dict') else d for d in data])
    
    cursor.execute("""
        INSERT OR REPLACE INTO weather_cache (lat, lng, date_start, date_end, data, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lat, lng, date_start, date_end, data_json, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()


def get_soil_moisture_cache(lat: float, lng: float, date_start: str, date_end: str) -> Optional[List[Dict[str, Any]]]:
    """Get cached soil moisture data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT data, created_at FROM soil_moisture_cache
        WHERE lat = ? AND lng = ? AND date_start = ? AND date_end = ?
    """, (lat, lng, date_start, date_end))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and is_cache_valid(row['created_at']):
        return json.loads(row['data'])
    return None


def set_soil_moisture_cache(lat: float, lng: float, date_start: str, date_end: str, data: List[Dict[str, Any]]):
    """Cache soil moisture data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data_json = json.dumps([d.dict() if hasattr(d, 'dict') else d for d in data])
    
    cursor.execute("""
        INSERT OR REPLACE INTO soil_moisture_cache (lat, lng, date_start, date_end, data, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lat, lng, date_start, date_end, data_json, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()


def get_ndvi_cache(field_id: str, date_start: str, date_end: str) -> Optional[Dict[str, Any]]:
    """Get cached NDVI data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT data, created_at FROM ndvi_cache
        WHERE field_id = ? AND date_start = ? AND date_end = ?
    """, (field_id, date_start, date_end))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and is_cache_valid(row['created_at']):
        return json.loads(row['data'])
    return None


def set_ndvi_cache(field_id: str, date_start: str, date_end: str, data: Dict[str, Any]):
    """Cache NDVI data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data_json = json.dumps(data.dict() if hasattr(data, 'dict') else data)
    
    cursor.execute("""
        INSERT OR REPLACE INTO ndvi_cache (field_id, date_start, date_end, data, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (field_id, date_start, date_end, data_json, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()


def cleanup_old_cache():
    """Remove expired cache entries"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cutoff_time = (datetime.now() - timedelta(hours=CACHE_TTL_HOURS * 2)).isoformat()
    
    cursor.execute("DELETE FROM weather_cache WHERE created_at < ?", (cutoff_time,))
    cursor.execute("DELETE FROM soil_moisture_cache WHERE created_at < ?", (cutoff_time,))
    cursor.execute("DELETE FROM ndvi_cache WHERE created_at < ?", (cutoff_time,))
    
    conn.commit()
    conn.close()


# Initialize database on import
init_db()

