from typing import Optional

from pydantic import BaseModel


class ArticleIn(BaseModel):
    


class LlmIn(BaseModel):
    texts: list[str]

class LlmOut(BaseModel):
    summarize_texts: list[str]


