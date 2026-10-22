import os
from typing import List
from pydantic_settings import BaseSettings

_env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

class Settings(BaseSettings):
    """Server configuration loaded from environment variables."""
    mongodb_uri: str = "mongodb://localhost:27017/carepoint"
    jwt_secret: str = "dev-secret-change-me"
    client_origin: str = "http://127.0.0.1:5173,http://localhost:5173"
    node_env: str = "development"
    port: int = 4000
    host: str = "0.0.0.0"

    @property
    def allowed_origins(self) -> List[str]:
        origins = [orig.strip() for orig in self.client_origin.split(",") if orig.strip()]
        for default_origin in ["http://localhost:5173", "http://127.0.0.1:5173"]:
            if default_origin not in origins:
                origins.append(default_origin)
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            origins.append(f"https://{vercel_url}")
        vercel_prod_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL")
        if vercel_prod_url:
            origins.append(f"https://{vercel_prod_url}")
        return origins

    class Config:
        env_file = _env_file
        extra = "ignore"

settings = Settings()
