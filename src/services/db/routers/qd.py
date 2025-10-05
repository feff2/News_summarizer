from fastapi import APIRouter, Request, HTTPException, status
from src.services.db.schemes import ArticleInsertRequest, SearchRequest, SearchResponse, SearchResult, DeleteResponse


router = APIRouter(prefix="/qdrant", tags=["qdrant"])


@router.post(
    "/embeddings",
    response_model=dict,
    summary="Вставить эмбеддинги в Qdrant",
    status_code=status.HTTP_201_CREATED
)
async def insert_embeddings_qdrant(
    request: Request,
    data: ArticleInsertRequest
) -> dict:
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.debug(f"Qdrant Insert: получено {len(data.embeddings)} эмбеддингов")
    
    try:
        # Конвертируем в словари
        articles_dict = [art.model_dump() for art in data.articles]
        
        # Добавляем db_id если есть (для связи с PostgreSQL)
        for i, art in enumerate(articles_dict):
            if 'id' in art:
                art['db_id'] = art['id']
        
        # Вставляем в Qdrant
        db_manager.upsert_embeddings(articles_dict, data.embeddings)
        
        logger.info(f"Qdrant Insert: успешно вставлено {len(data.embeddings)} эмбеддингов")
        
        return {
            "success": True,
            "inserted_count": len(data.embeddings),
            "message": "Эмбеддинги успешно сохранены в Qdrant"
        }
        
    except Exception as e:
        logger.error(f"Qdrant Insert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка вставки в Qdrant: {str(e)}"
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Поиск похожих статей в Qdrant"
)
async def search_similar_qdrant(
    request: Request,
    data: SearchRequest
) -> SearchResponse:
    """
    Семантический поиск похожих статей в Qdrant
    
    Args:
        data: Вектор запроса и параметры поиска
        
    Returns:
        Список похожих статей
    """
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.debug(
        f"Qdrant Search: vector_dim={len(data.query_vector)}, "
        f"limit={data.limit}, threshold={data.score_threshold}"
    )
    
    try:
        results = db_manager.search_similar(
            query_vector=data.query_vector,
            limit=data.limit,
            score_threshold=data.score_threshold
        )
        
        logger.info(f"Qdrant Search: найдено {len(results)} результатов")
        
        search_results = [
            SearchResult(
                id=r["id"],
                score=r["score"],
                payload=r["payload"]
            )
            for r in results
        ]
        
        return SearchResponse(
            results=search_results,
            total=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Qdrant Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка поиска в Qdrant: {str(e)}"
        )


@router.delete(
    "/embeddings/{article_id}",
    response_model=DeleteResponse,
    summary="Удалить эмбеддинг из Qdrant"
)
async def delete_embedding_qdrant(
    request: Request,
    article_id: int
) -> DeleteResponse:
    """
    Удаление эмбеддинга из Qdrant
    
    Args:
        article_id: ID статьи
        
    Returns:
        Статус удаления
    """
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.debug(f"Qdrant Delete: article_id={article_id}")
    
    try:
        client = db_manager.get_qdrant_client()
        client.delete(
            collection_name=db_manager.collection_name,
            points_selector=[article_id]
        )
        
        logger.info(f"Qdrant Delete: эмбеддинг {article_id} удален")
        
        return DeleteResponse(
            success=True,
            message=f"Эмбеддинг {article_id} успешно удален из Qdrant"
        )
        
    except Exception as e:
        logger.error(f"Qdrant Delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления из Qdrant: {str(e)}"
        )
