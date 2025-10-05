from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ArticleIn(BaseModel):
    url: str
    summary: str = ""
    published_at: datetime


class ArticleOut(BaseModel):
    id: int
    summary: str
    published_at: datetime
    created_at: Optional[datetime] = None


class ArticleInsertRequest(BaseModel):
    articles: List[ArticleIn]
    embeddings: List[List[float]]


class ArticleInsertResponse(BaseModel):
    articles: List[ArticleOut]
    inserted_count: int


class ArticlesListResponse(BaseModel):
    articles: List[ArticleOut]
    total: int


class SearchRequest(BaseModel):
    query_vector: List[float]
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    id: int
    score: float
    payload: dict


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int


class DeleteResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    postgres: bool
    qdrant: bool