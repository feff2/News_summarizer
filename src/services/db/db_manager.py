import os
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
        conn = conn = psycopg2.connect(
            host=os.getenv("DATABASE_HOST", "postgres"),
            port=os.getenv("DATABASE_PORT", 5432),
            user=os.getenv("DATABASE_USER", "postgres"),
            password=os.getenv("DATABASE_PASSWORD", "mysecret"),
            dbname=os.getenv("DATABASE_NAME", "news_db")
        )
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
    
    def insert_cluster(self, cluster_data: dict) -> int:
        """
        Вставить кластер новостей и связи с статьями
        
        Args:
            cluster_data: {
                'summary': str,
                'cluster_label': int,
                'members_count': int,
                'article_ids': List[int],
                'representative_ids': List[int]
            }
            
        Returns:
            ID созданного кластера
        """
        with self.pg_connection() as conn:
            cur = conn.cursor()
            
            # Вставляем кластер
            cur.execute("""
                INSERT INTO news_clusters (summary, cluster_label, members_count)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                cluster_data['summary'],
                cluster_data['cluster_label'],
                cluster_data['members_count']
            ))
            
            cluster_id = cur.fetchone()[0]
            
            # Вставляем связи с статьями
            article_ids = cluster_data['article_ids']
            representative_ids = set(cluster_data.get('representative_ids', []))
            
            for article_id in article_ids:
                is_representative = article_id in representative_ids
                cur.execute("""
                    INSERT INTO cluster_articles (cluster_id, article_id, is_representative)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (cluster_id, article_id) DO NOTHING
                """, (cluster_id, article_id, is_representative))
            
            cur.close()
            self._logger.info(f"Inserted cluster {cluster_id} with {len(article_ids)} articles")
            return cluster_id
    
    def get_clusters(
        self,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at DESC"
    ) -> List[dict]:
        """Получить список кластеров с представителями"""
        with self.pg_connection() as conn:
            cur = conn.cursor()
            
            # Получаем кластеры
            cur.execute(f"""
                SELECT id, summary, cluster_label, members_count, created_at, updated_at
                FROM news_clusters
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            clusters = []
            for row in cur.fetchall():
                cluster_id = row[0]
                
                # Получаем представителей кластера
                cur.execute("""
                    SELECT n.id, n.title, n.url, n.published_at
                    FROM news n
                    JOIN cluster_articles ca ON n.id = ca.article_id
                    WHERE ca.cluster_id = %s AND ca.is_representative = TRUE
                    ORDER BY n.published_at DESC
                """, (cluster_id,))
                
                representatives = [
                    {
                        'article_id': r[0],
                        'title': r[1],
                        'url': r[2],
                        'published_at': r[3]
                    }
                    for r in cur.fetchall()
                ]
                
                # Получаем все ID статей кластера
                cur.execute("""
                    SELECT article_id
                    FROM cluster_articles
                    WHERE cluster_id = %s
                """, (cluster_id,))
                
                article_ids = [r[0] for r in cur.fetchall()]
                
                clusters.append({
                    'id': row[0],
                    'summary': row[1],
                    'cluster_label': row[2],
                    'members_count': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'representatives': representatives,
                    'article_ids': article_ids
                })
            
            cur.close()
            return clusters
    
    def get_cluster_by_id(self, cluster_id: int) -> Optional[dict]:
        """Получить кластер по ID"""
        clusters = self.get_clusters(limit=1, offset=0, order_by=f"id = {cluster_id} DESC")
        return clusters[0] if clusters else None
    
    def delete_cluster(self, cluster_id: int) -> bool:
        """Удалить кластер (связи удалятся автоматически по CASCADE)"""
        with self.pg_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM news_clusters WHERE id = %s", (cluster_id,))
            deleted = cur.rowcount > 0
            cur.close()
            return deleted

    def close(self):
        if self._qdrant_client:
            self._qdrant_client.close()
            self._qdrant_client = None