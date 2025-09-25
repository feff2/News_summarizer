import os
from pydantic import BaseModel


class CroneSettings(BaseModel):
    NEWS_API: list[str] = ["https://example.com/api/news"]
    BATCH_SIZE: int = 10

    PG_CONN: dict = 
        {
            "dbname": os.getenv("PG_DB", "newsdb"),
            "user": os.getenv("PG_USER", "user"),
            "password": os.getenv("PG_PASS", "pass"),
            "host": os.getenv("PG_HOST", "localhost"),
            "port": 5432
        }

    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION: str = "news_embeddings"

    LLM_API: str = os.getenv("LLM_API", "http://localhost:8000")
    EMBEDDER_API: str = os.getenv("EMBEDDER_API", "http://localhost:8001")
