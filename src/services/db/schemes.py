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

class ArticleBase(BaseModel):
    url: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    source: Optional[str] = None


class ArticleInsert(ArticleBase):
    """Схема для вставки статьи"""
    pass


class ArticleOut(ArticleBase):
    """Выходная схема статьи"""
    id: int
    created_at: datetime


class ArticleInsertRequest(BaseModel):
    """Запрос на вставку статей"""
    articles: List[ArticleInsert]


class ArticleInsertResponse(BaseModel):
    """Ответ на вставку статей"""
    articles: List[ArticleOut]
    inserted_count: int


class ClusterRepresentative(BaseModel):
    """Представитель кластера (краткая инфа о статье)"""
    article_id: int
    title: str
    url: str
    published_at: Optional[datetime]

class NewsClusterCreate(BaseModel):
    """Создание нового кластера новостей"""
    summary: str
    cluster_label: int
    members_count: int
    article_ids: List[int]  # Все статьи в кластере
    representative_ids: List[int]  # ID представителей

class NewsClusterOut(BaseModel):
    """Выходная схема кластера"""
    id: int
    summary: str
    cluster_label: int
    members_count: int
    created_at: datetime
    updated_at: datetime
    representatives: List[ClusterRepresentative]
    article_ids: List[int]

class ClustersListResponse(BaseModel):
    """Список кластеров"""
    clusters: List[NewsClusterOut]
    total: int