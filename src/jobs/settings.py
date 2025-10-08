import os
import torch
from typing import ClassVar, Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    BATCH_SIZE: int = Field(4, description="Default batch size for processing")
    RSS_URLS: ClassVar[List[str]] = ["https://lenta.ru/rss"]

    DB_URL: str = Field("http://localhost:8001", env="DB_URL")
    PG_INSERT_ENDPOINT: str = Field("articles", env="PG_INSERT_ENDPOINT")
    QD_INSERT_ENDPOINT: str = Field("embeddings", env="QD_INSERT_ENDPOINT")
    COLLECTION: str = Field("news_embeddings", env="COLLECTION")
    PG_CONFIG: Dict[str, str] = Field(
        default_factory=lambda: {
            "host": os.getenv("PG_HOST", "localhost"),
            "database": os.getenv("PG_DATABASE", "news_db"),
            "user": os.getenv("PG_USER", "news_summarizer"),
            "password": os.getenv("PG_PASSWORD", ""),
        }
    )

    INFERENCE_HOST: str = Field("localhost", env="INFERENCE_HOST")
    INFERENCE_PORT: int = Field(9004, env="INFERENCE_PORT")
    INFERENCE_TIMEOUT_S: int = Field(10, env="INFERENCE_TIMEOUT_S")
    MAX_QUEUE_DELAY_MICROSECONDS: int = Field(10, env="MAX_QUEUE_DELAY_MICROSECONDS")
    MAX_BATCH_SIZE: int = Field(8, env="MAX_BATCH_SIZE")
    BATCH_WINDOW_MS: int = Field(1000, env="BATCH_WINDOW_MS")

    MODEL_PATH: str = Field("models/embeder/multilingual-e5-base", env="EMBEDDER_MODEL_PATH")
    EMBEDDER_MODEL_NAME: str = Field("multilingual-e5-base", env="EMBEDDER_MODEL_NAME")
    MODEL_NAME_FORMAT: str = Field("torch", env="MODEL_NAME_FORMAT")

    USE_GPU: bool = Field(default=torch.cuda.is_available(), env="USE_GPU")
    GPU_INDEX: int = Field(0, env="GPU_INDEX")

    LLM_MODEL_PATH: str = Field("models/llm/Qwen3-1.7B", env="LLM_MODEL_PATH")
    MODE: str = Field("vllm", env="MODE")
    LLM_PORT: int = Field(8080, env="LLM_PORT")
    MAX_CONCURRENCY: int = Field(100, env="MAX_CONCURRENCY")
    REQUEST_TIMEOUT: int = Field(10, env="REQUEST_TIMEOUT")
    PARAMS: Dict = Field(default_factory=lambda: {"top_k": 100, "temperature": 1.0})
    SYSTEM_PROMPT: str = Field(
        "Ты опытный и точный ассистент, который обращает огромное внимание на контекст, который получает. "
        "В случае если ты неуверен в ответе, скажи пользователю: "
        "'Извините, я не могу помочь с этим вопросом, но готов ответить на другие'.",
        env="SYSTEM_PROMPT",
    )

    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")
    HISTORY_MAX_TOKENS: int = Field(10000, env="HISTORY_MAX_TOKENS")
    RELOAD: bool = Field(True, env="RELOAD")

    DEVICE: Optional[torch.device] = None

    class Config:
        env_prefix = ""
        case_sensitive = False

    def __init__(self, **values):
        super().__init__(**values)

        if self.USE_GPU and torch.cuda.is_available():
            gpu_idx = int(self.GPU_INDEX) if isinstance(self.GPU_INDEX, int) or str(self.GPU_INDEX).isdigit() else 0
            self.DEVICE = torch.device(f"cuda:{gpu_idx}")
        else:
            self.DEVICE = torch.device("cpu")

    @property
    def inference_url(self) -> str:
        return f"http://{self.INFERENCE_HOST}:{self.INFERENCE_PORT}"

    @property
    def llm_url(self) -> str:
        return f"http://{self.INFERENCE_HOST}:{self.LLM_PORT}{self.API_V1_STR}"

    def pg_dsn(self) -> str:
        cfg = self.PG_CONFIG
        pwd = cfg.get("password") or ""
        return f"postgresql://{cfg.get('user')}:{pwd}@{cfg.get('host')}/{cfg.get('database')}"


settings = Settings()
