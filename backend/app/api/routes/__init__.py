# API routes package
# Explicitly export all routers for easier imports

from . import farms, crops, fields, ndvi, weather, soil, kpi, yield_prediction, carbon

__all__ = ['farms', 'crops', 'fields', 'ndvi', 'weather', 'soil', 'kpi', 'yield_prediction', 'carbon']
