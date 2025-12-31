"""
Application configuration
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Copernicus Data Space API
    copernicus_client_id: str = ""
    copernicus_client_secret: str = ""
    
    # Copernicus CDS API
    cds_url: str = "https://cds.climate.copernicus.eu/api"
    cds_key: str = ""
    
    # FAO API
    fao_api_base_url: str = "https://fenixservices.fao.org/faostat/api/v1/en"
    
    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"  # Comma-separated list
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Data Cache
    cache_dir: str = "./cache"
    cache_ttl: int = 3600
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_file_encoding": "utf-8"
    }


settings = Settings()

