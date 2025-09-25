import torch

from src.shared.settings import SharedSettings


class Settings(SharedSettings):
    INFERENCE_HOST: str = "localhost"
    MODEL_NAME_PORT: int = 9004

    MODEL_NAME_PATH: str = "/app/models/bi_encoder/all-MiniLM-L6-v2"
    MODEL_NAME_NAME: str = "all_MiniLM_L6_v2"

    MODEL_NAME_FORMAT: str = "torch"

    INFERENCE_TIMEOUT_S: int = 10
    MAX_QUEUE_DELAY_MICROSECONDS: int = 10
    MAX_BATCH_SIZE: int = 8
    GPU_INDEX: int = 0

    API_V1_STR: str = "/api/v1"

    DEVICE: torch.device = torch.device("cuda:0") if torch.cuda.is_available else torch.device("cpu")


settings = Settings()