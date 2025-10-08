import httpx
from typing import List, Dict, Optional
from src.shared.logger import LoggerWrapper

class NewsApiClient:
    """Клиент для общения с API базы данных"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = LoggerWrapper("api_client")
    
    async def insert_articles(self, articles: List[Dict]) -> List[Dict]:
        articles_payload = []
        for a in articles:
            if not a.get("url") or not a.get("published_at"):
                continue
            articles_payload.append({
                "url": a["url"],
                "summary": a.get("summary", a.get("content", "")),
                "published_at": a.get("published_at") if isinstance(a.get("published_at"), str) else a.get("published_at").isoformat()
            })
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                import json
                print(json.dumps({"articles": articles_payload}, indent=2))
                response = await client.post(
                    f"{self.base_url}/pg/articles",
                    json={"articles": articles}
                )
                response.raise_for_status()
                result = response.json()
                
                self.logger.info(f"Inserted {result['inserted_count']} articles via API")
                return result['articles']
                
            except httpx.HTTPError as e:
                self.logger.error(f"Failed to insert articles: {e}")
                raise
    
    async def insert_embeddings(self, articles: List[Dict], embeddings: List[List[float]]) -> Dict:
        """
        Вставить эмбеддинги в Qdrant через API
        
        Args:
            articles: Список статей (должны содержать поле 'id' из PostgreSQL)
            embeddings: Список векторов эмбеддингов
            
        Returns:
            Результат операции
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/qdrant/embeddings",
                    json={
                        "articles": articles,
                        "embeddings": embeddings
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                self.logger.info(f"Inserted {result['inserted_count']} embeddings via API")
                return result
                
            except httpx.HTTPError as e:
                self.logger.error(f"Failed to insert embeddings: {e}")
                raise
    
    async def create_cluster(self, cluster_data: Dict) -> Dict:
        """
        Создать кластер (инфоповод) через API
        
        Args:
            cluster_data: {
                'summary': str,
                'cluster_label': int,
                'members_count': int,
                'article_ids': List[int],
                'representative_ids': List[int]
            }
            
        Returns:
            Созданный кластер
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    "localhost:8003/api/v1/pg/clusters",
                    json=cluster_data
                )
                response.raise_for_status()
                result = response.json()
                
                self.logger.info(f"Created cluster {result['id']} via API")
                return result
                
            except httpx.HTTPError as e:
                self.logger.error(f"Failed to create cluster: {e}")
                raise
    
    async def get_articles(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Получить статьи из БД через API"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/pg/articles",
                    params={"limit": limit, "offset": offset}
                )
                response.raise_for_status()
                result = response.json()
                
                return result['articles']
                
            except httpx.HTTPError as e:
                self.logger.error(f"Failed to get articles: {e}")
                raise
    
    async def get_clusters(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Получить кластеры из БД через API"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/clusters",
                    params={"limit": limit, "offset": offset}
                )
                response.raise_for_status()
                result = response.json()
                
                return result['clusters']
                
            except httpx.HTTPError as e:
                self.logger.error(f"Failed to get clusters: {e}")
                raise