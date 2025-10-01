import os
from pydantic import BaseModel


class Settings(BaseModel):
    QDRANT_API: str = os.getenv("QDRANT_API")
    POSTGRES_API: str = (os.getenv("POSTGRES_API"))
    API_HOST: str = "localhost"
    API_PORT: int = 8080
    RELOAD: bool = True
    API_V1_STR: str = "/api/v1"


settings = Settings()