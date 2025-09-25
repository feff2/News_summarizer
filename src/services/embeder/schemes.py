from typing import List
from pydantic import BaseModel, Field

from torch import Tensor


class EncodeIn(BaseModel):
    texts: List[str] = Field("Привет", description="Текст для кодирования")


class EncodeOut(BaseModel):
    vectors: List[Tensor] = Field(..., description="Эмбединг текста")
