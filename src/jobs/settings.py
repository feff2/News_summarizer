from pydantic import BaseModel, Field


class CroneSettings(BaseModel):
    NEWS_API: list[str] = Field(["https://example.com/api/news"])
    BATCH_SIZE: int = Field(10)

    PG_CONN: dict = Field(
        {
            "dbname": os.getenv("PG_DB", "newsdb"),
            "user": os.getenv("PG_USER", "user"),
            "password": os.getenv("PG_PASS", "pass"),
            "host": os.getenv("PG_HOST", "localhost"),
            "port": 5432
        }
    )

    QDRANT_HOST: str = Field(os.getenv("QDRANT_HOST", "localhost"))
    QDRANT_PORT: int = Field(int(os.getenv("QDRANT_PORT", "6333")))
    COLLECTION: str = Field("news_embeddings")

    LLM_API: str = Field(os.getenv("LLM_API", "http://localhost:8000"))
    EMBEDDER_API: str = Field(os.getenv("EMBEDDER_API", "http://localhost:8001"))
