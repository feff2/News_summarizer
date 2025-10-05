import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class DatabaseManager:
    def __init__(
        self,
        pg_config: Dict[str, Any],
        qdrant_host: str,
        qdrant_port: int = 6333,
        collection_name: str = "news_embeddings"
    ):
        self.pg_config = pg_config
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = collection_name
        
        self._pg_conn = None
        self._qdrant_client = None
    
    @contextmanager
    def pg_connection(self):
        conn = psycopg2.connect(**self.pg_config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def create_news_table(self):
        with self.pg_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    url TEXT UNIQUE,
                    content TEXT,
                    summary TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.close()
    
    def insert_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        with self.pg_connection() as conn:
            cur = conn.cursor()
            
            for art in articles:
                try:
                    cur.execute(
                        """
                        INSERT INTO news (title, url, content, summary, published_at) 
                        VALUES (%s, %s, %s, %s, %s) 
                        RETURNING id
                        """,
                        (
                            art.get("title"),
                            art.get("url"),
                            art.get("content"),
                            art.get("summary"),
                            art.get("published_at")
                        )
                    )
                    art["db_id"] = cur.fetchone()[0]
                except psycopg2.IntegrityError:
                    conn.rollback()
                    continue
            
            cur.close()
        
        return [a for a in articles if "db_id" in a]
    
    def get_articles(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "published_at DESC"
    ) -> List[Dict[str, Any]]:
        with self.pg_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                f"""
                SELECT * FROM news 
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )
            results = cur.fetchall()
            cur.close()
            return [dict(row) for row in results]
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        with self.pg_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM news WHERE id = %s", (article_id,))
            result = cur.fetchone()
            cur.close()
            return dict(result) if result else None
    
    def get_qdrant_client(self) -> QdrantClient:
        if self._qdrant_client is None:
            self._qdrant_client = QdrantClient(
                host=self.qdrant_host,
                port=self.qdrant_port
            )
        return self._qdrant_client
    
    def create_collection(self, vector_size: int = 768, distance: Distance = Distance.COSINE):
        client = self.get_qdrant_client()
        
        collections = client.get_collections().collections
        if any(c.name == self.collection_name for c in collections):
            return
        
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance)
        )
    
    def upsert_embeddings(
        self,
        articles: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        client = self.get_qdrant_client()
        
        points = [
            PointStruct(
                id=art["db_id"],
                vector=vec,
                payload={
                    "title": art.get("title", ""),
                    "summary": art.get("summary", ""),
                    "published_at": str(art.get("published_at", "")),
                    "url": art.get("url", "")
                }
            )
            for art, vec in zip(articles, embeddings)
            if "db_id" in art
        ]
        
        if points:
            client.upsert(collection_name=self.collection_name, points=points)
    
    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        client = self.get_qdrant_client()
        
        results = client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]
    
    def delete_by_id(self, article_id: int):
        client = self.get_qdrant_client()
        client.delete(
            collection_name=self.collection_name,
            points_selector=[article_id]
        )
        
        with self.pg_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM news WHERE id = %s", (article_id,))
            cur.close()
    
    def close(self):
        if self._qdrant_client:
            self._qdrant_client.close()
            self._qdrant_client = None