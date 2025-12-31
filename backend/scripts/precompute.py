#!/usr/bin/env python3
"""
Standalone script to precompute KPI, Weather, and Soil data
Can be run via cron or scheduled task

Usage:
    python -m app.services.precompute
    or
    python scripts/precompute.py
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.precompute import precompute_all_fields


if __name__ == "__main__":
    print("Starting precomputation...")
    asyncio.run(precompute_all_fields())
    print("Precomputation complete!")

