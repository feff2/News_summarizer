import torch


class Settings():
    INFERENCE_HOST: str = "localhost"
    INFERENCE_PORT: int = 9004

    MODEL_PATH: str = "/app/models/embeder/bge-m3"
    MODEL_NAME: str = "bge-m3"

    MODEL_NAME_FORMAT: str = "torch"

    INFERENCE_TIMEOUT_S: int = 10
    MAX_QUEUE_DELAY_MICROSECONDS: int = 10
    MAX_BATCH_SIZE: int = 8
    USE_GPU: bool= True if torch.cuda.is_available else False
    GPU_INDEX: int = 0

    API_V1_STR: str = "/api/v1"
    RELOAD: bool = True


settings = Settings()