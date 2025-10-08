import math
from datetime import datetime, timezone
from typing import List, Dict, Optional

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

import torch
import asyncio

from .api_client import NewsApiClient
from .models.embeder.embeder import E5Embedder
from .models.llm.llm_client import LlmClient
from .settings import settings
from .scrapers import RssScraper
from src.shared.logger import LoggerWrapper

log = LoggerWrapper("news_update_job")


def dedupe_by_url(articles: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for a in articles:
        url = a.get("url") or a.get("link") or ""
        if url in seen:
            continue
        seen.add(url)
        out.append(a)
    return out


def parse_published_at(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s) if "T" in s else datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def fetch_news(rss_scraper, n):
    return rss_scraper.scrape_feed(settings.RSS_URLS, limit=3)


def compute_embeddings_for_articles(articles, embeder):
    texts = [a.get("content") or a.get("title") or "" for a in articles]
    embeddings = embeder.encode(texts, normalize_embeddings=True)

    if embeddings.size > 0:
        return embeddings
    return np.zeros((0, 0), dtype=np.float32)


def cluster_embeddings_dbscan(embeddings: np.ndarray, eps: float = 0.25, min_samples: int = 1) -> np.ndarray:
    if embeddings.shape[0] == 0:
        return np.array([], dtype=int)
    emb_norm = normalize(embeddings, axis=1)
    db = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine", n_jobs=-1)
    labels = db.fit_predict(emb_norm)
    return labels


def choose_representatives(
    articles: List[Dict],
    embeddings: np.ndarray,
    labels: np.ndarray,
    max_per_cluster: int = 3,
    recency_weight: float = 0.3
) -> Dict[int, List[int]]:
    idxs_by_cluster = {}
    emb_norm = normalize(embeddings, axis=1)
    unique_labels = sorted(set(labels.tolist()))
    now = datetime.now(timezone.utc)

    for label in unique_labels:
        if label == -1:
            continue
        idxs = np.where(labels == label)[0]
        cluster_embs = emb_norm[idxs]
        centroid = cluster_embs.mean(axis=0, keepdims=True)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-12)

        sims = cosine_similarity(cluster_embs, centroid).flatten()

        recency = []
        for i in idxs:
            published = parse_published_at(articles[i].get("published_at"))
            if published is None:
                recency.append(0.0)
            else:
                seconds = (now - published).total_seconds()
                recency.append(1.0 / (1.0 + math.log1p(seconds + 1e-9)))
        recency = np.asarray(recency)

        sims_n = (sims - sims.min()) / (sims.max() - sims.min() + 1e-12)
        recency_n = (recency - recency.min()) / (recency.max() - recency.min() + 1e-12)

        score = (1.0 - recency_weight) * sims_n + recency_weight * recency_n
        order = np.argsort(-score)
        idxs_by_cluster[label] = idxs[order][:max_per_cluster].tolist()

    return idxs_by_cluster


def summarize_cluster_texts(articles: List[Dict], chosen_idxs: List[int], llm) -> str:
    parts = []
    for i in chosen_idxs:
        a = articles[i]
        text = a.get("summary") or a.get("content") or a.get("title") or ""
        header = f"Title: {a.get('title','')}\nURL: {a.get('url','')}\nPublished: {a.get('published_at','')}\n"
        parts.append(header + "\n" + text)
    combined = "\n\n---\n\n".join(parts)

    max_len_chars = 60_000
    if len(combined) > max_len_chars:
        combined = combined[:max_len_chars]

    return llm.generate(combined)


async def pipeline_run(
    n_fetch: int = 50,
    cluster_eps: float = 0.25,
    min_cluster_size: int = 1,
    max_representatives: int = 3,
    embed_batch_size: int = 32,
    api_base_url: str = "http://localhost:8000"  # URL API
):
    log.info("Starting pipeline...")
    
    # Инициализируем API клиент
    api_client = NewsApiClient(base_url=api_base_url)
    
    rss_scraper = RssScraper()
    
    # ===== ШАГ 1: Получение и сохранение новостей =====
    log.info("Fetching news...")
    articles_dict = await asyncio.to_thread(fetch_news, rss_scraper, n_fetch)
    
    articles_with_content = []
    for source, articles in articles_dict.items():
        articles = dedupe_by_url(articles)
        articles = [a for a in articles if a.get("content")]
        articles_with_content.extend(articles)
        log.info(f"Source '{source}' -> {len(articles)} articles after dedupe/filtering")
    
    if not articles_with_content:
        log.info("No articles with content found")
        return
    
    # Сохраняем статьи в PostgreSQL через API
    log.info(f"Saving {len(articles_with_content)} articles to database via API...")
    saved_articles = await api_client.insert_articles(articles_with_content)
    
    # Обновляем articles_with_content с ID из БД
    for i, article in enumerate(articles_with_content):
        if i < len(saved_articles):
            article['db_id'] = saved_articles[i]['id']
    
    # ===== ШАГ 2: Вычисление эмбеддингов =====
    log.info("Loading e5 encoder...")
    encoder = await asyncio.to_thread(
        E5Embedder, 
        device=settings.DEVICE,
    )
    log.info("e5 encoder loaded!")
    
    log.info(f"Computing embeddings for {len(articles_with_content)} articles...")
    embeddings = compute_embeddings_for_articles(articles_with_content, embeder=encoder)
    
    if embeddings.shape[0] != len(articles_with_content):
        log.warning(f"Embeddings count mismatch: {embeddings.shape[0]} vs {len(articles_with_content)}")
    
    # Сохраняем эмбеддинги в Qdrant через API
    log.info("Saving embeddings to Qdrant via API...")
    embeddings_list = embeddings.tolist()
    await api_client.insert_embeddings(saved_articles, embeddings_list)
    
    # Освобождаем память
    del encoder
    torch.cuda.empty_cache()
    
    # ===== ШАГ 3: Кластеризация =====
    log.info(f"Clustering embeddings (eps={cluster_eps})...")
    labels = cluster_embeddings_dbscan(embeddings, eps=cluster_eps, min_samples=min_cluster_size)
    n_clusters = len(set(labels.tolist()) - {-1})
    log.info(f"Clusters found: {n_clusters}, noise_count={(labels == -1).sum()}")
    
    reps = choose_representatives(
        articles_with_content, 
        embeddings, 
        labels, 
        max_per_cluster=max_representatives
    )
    log.info(f"Representatives chosen for {len(reps)} clusters")
    
    # ===== ШАГ 4: Генерация саммари =====
    log.info("Loading vLLM client...")
    llm = await asyncio.to_thread(
        LlmClient,
        model_name=settings.LLM_MODEL_PATH,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        params={"max_tokens": 256, "temperature": 0.7},
        system_prompt="You are a helpful news summarization assistant. Create concise summaries.",
        logger=LoggerWrapper("llm_client"),
    )
    log.info("vLLM client loaded!")
    
    # ===== ШАГ 5: Создание кластеров через API =====
    created_clusters = []
    
    for label, chosen_idxs in reps.items():
        log.info(f"Processing cluster {label}...")
        
        # Генерируем саммари
        summary_text = summarize_cluster_texts(articles_with_content, chosen_idxs, llm)
        
        # Получаем ID представителей
        representative_ids = []
        for i in chosen_idxs:
            db_id = articles_with_content[i].get("db_id")
            if db_id:
                representative_ids.append(db_id)
        
        # Получаем все ID статей в кластере
        cluster_indices = np.where(labels == label)[0]
        all_article_ids = []
        for i in cluster_indices:
            db_id = articles_with_content[i].get("db_id")
            if db_id:
                all_article_ids.append(db_id)
        
        cluster_data = {
            "summary": summary_text,
            "cluster_label": int(label),
            "members_count": int((labels == label).sum()),
            "article_ids": all_article_ids,
            "representative_ids": representative_ids
        }
        
        try:
            created_cluster = await api_client.create_cluster(cluster_data)
            created_clusters.append(created_cluster)
            log.info(f"Cluster {label} created with ID {created_cluster['id']}")
            log.info(f"Summary preview: {summary_text[:100]}...")
        except Exception as e:
            log.error(f"Failed to create cluster {label}: {e}")
    
    llm.close()
    log.info("Pipeline completed!")
    
    return {
        "articles_count": len(articles_with_content),
        "clusters_found": n_clusters,
        "clusters_created": len(created_clusters),
        "clusters": created_clusters
    }


if __name__ == "__main__":
    import asyncio
    
    res = asyncio.run(
        pipeline_run(
            n_fetch=100,
            cluster_eps=0.25,
            min_cluster_size=2,
            max_representatives=3,
            api_base_url="http://localhost:8001/api/v1"
        )
    )
    
    print(f"Done: {res['articles_count']} articles")
    print(f"Found: {res['clusters_found']} clusters")
    print(f"Created: {res['clusters_created']} clusters")