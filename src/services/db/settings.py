import os
from typing import ClassVar
from pydantic import BaseModel


class Settings(BaseModel):
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    PG_CONFIG: ClassVar[dict[str, str]] = {
        "host": "localhost",
        "database": "news_db",
        "user": "news_summarizer",
        "password": os.getenv("pg_password")
    }
    COLLECTION_NAME: str = "news_embedings"
    API_HOST: str = "localhost"
    API_PORT: int = 8001
    RELOAD: bool = True
    API_V1_STR: str = "/api/v1"


settings = Settings()