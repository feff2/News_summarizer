from pydantic import BaseModel


class Settings(BaseModel):
    DB_URL: str = "http://localhost:8001"
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    RELOAD: bool = True
    API_V1_STR: str = "/api/v1"


settings = Settings()