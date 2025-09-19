import os
import datetime
import psycopg2
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


def fetch_news(n: int):
    resp = requests.get(NEWS_API, params={"limit": n})
    resp.raise_for_status()
    return resp.json()["articles"]


def summarize(text: str) -> str:
    resp = requests.post(f"{LLM_API}/summarize", json={"text": text})
    resp.raise_for_status()
    return resp.json()["summary"]


def embed_texts(texts: list[str]):
    resp = requests.post(f"{EMBEDDER_API}/encode", json={"texts": texts})
    resp.raise_for_status()
    return resp.json()["embeddings"]


def save_to_postgres(articles):
    conn = psycopg2.connect(**PG_CONN)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            summary TEXT,
            published_at TIMESTAMP
        );
    """)
    for art in articles:
        cur.execute(
            "INSERT INTO news (title, content, summary, published_at) VALUES (%s, %s, %s, %s) RETURNING id",
            (art["title"], art["content"], art["summary"], art["published_at"])
        )
        art["db_id"] = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return articles


def save_to_qdrant(articles, embeddings):
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    points = [
        PointStruct(
            id=art["db_id"],
            vector=vec,
            payload={
                "title": art["title"],
                "summary": art["summary"],
                "published_at": art["published_at"]
            }
        )
        for art, vec in zip(articles, embeddings)
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points)


if __name__ == "__main__":
    articles = fetch_news(BATCH_SIZE)

    for a in articles:
        a["summary"] = summarize(a["content"])

    embeddings = embed_texts([a["content"] for a in articles])
    enriched = save_to_postgres(articles)
    save_to_qdrant(enriched, embeddings)

    print(f"Inserted {len(articles)} articles at {datetime.datetime.utcnow()}")
