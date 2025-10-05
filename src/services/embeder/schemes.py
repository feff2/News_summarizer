from typing import List
from pydantic import BaseModel, Field


class EncodeIn(BaseModel):
    texts: List[str] = Field("Привет", description="Текст для кодирования")


class EncodeOut(BaseModel):
    vectors: List[float] = Field(..., description="Эмбединг текста")
