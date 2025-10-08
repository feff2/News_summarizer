from fastapi import APIRouter, Request, HTTPException, status
from ..schemes import ArticleInsertRequest, ArticleInsertResponse, ArticleOut, ArticlesListResponse, DeleteResponse, NewsClusterCreate, NewsClusterOut


router = APIRouter(prefix="/pg", tags=["postgres"])


@router.post(
    "clusters",
    response_model=NewsClusterOut,
    summary="Создать новый кластер новостей",
    status_code=status.HTTP_201_CREATED
)
async def create_cluster(
    request: Request,
    data: NewsClusterCreate
) -> NewsClusterOut:
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.info(f"Create cluster: label={data.cluster_label}, articles={len(data.article_ids)}")
    
    try:
        cluster_dict = data.model_dump()
        cluster_id = db_manager.insert_cluster(cluster_dict)
        
        cluster = db_manager.get_cluster_by_id(cluster_id)
        
        if cluster is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created cluster"
            )
        
        logger.info(f"Created cluster {cluster_id} with {data.members_count} members")
        
        return NewsClusterOut(**cluster)
        
    except Exception as e:
        logger.error(f"Create cluster error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания кластера: {str(e)}"
        )


@router.post(
    "/articles",
    response_model=ArticleInsertResponse,
    summary="Вставить статьи в PostgreSQL",
    status_code=status.HTTP_201_CREATED
)
async def insert_articles_pg(
    request: Request,
    data: ArticleInsertRequest
) -> ArticleInsertResponse:
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.info(f"PG Insert: получено {len(data.articles)} статей")
    
    try:
        articles_dict = [art.model_dump() for art in data.articles]
        
        # Вставляем в PostgreSQL
        inserted = db_manager.insert_articles(articles_dict)
        
        logger.info(f"PG Insert: успешно вставлено {len(inserted)} статей")
        
        return ArticleInsertResponse(
            articles=[ArticleOut(**art) for art in inserted],
            inserted_count=len(inserted)
        )
        
    except Exception as e:
        logger.error(f"PG Insert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка вставки в PostgreSQL: {str(e)}"
        )


@router.get(
    "/articles",
    response_model=ArticlesListResponse,
    summary="Получить список статей из PostgreSQL"
)
async def get_articles_pg(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "published_at DESC"
) -> ArticlesListResponse:
    """
    Получение статей из PostgreSQL с пагинацией
    
    Args:
        limit: Количество статей
        offset: Смещение
        order_by: Поле для сортировки
        
    Returns:
        Список статей
    """
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.info(f"PG Get: limit={limit}, offset={offset}, order_by={order_by}")
    
    try:
        articles = db_manager.get_articles(
            limit=limit,
            offset=offset,
            order_by=order_by
        )
        
        logger.info(f"PG Get: получено {len(articles)} статей")
        
        return ArticlesListResponse(
            articles=[ArticleOut(**art) for art in articles],
            total=len(articles)
        )
        
    except Exception as e:
        logger.error(f"PG Get error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения из PostgreSQL: {str(e)}"
        )


@router.get(
    "/articles/{article_id}",
    response_model=ArticleOut,
    summary="Получить статью по ID из PostgreSQL"
)
async def get_article_by_id_pg(
    request: Request,
    article_id: int
) -> ArticleOut:
    """
    Получение статьи по ID из PostgreSQL
    
    Args:
        article_id: ID статьи
        
    Returns:
        Статья
    """
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.info(f"PG Get by ID: article_id={article_id}")
    
    try:
        article = db_manager.get_article_by_id(article_id)
        
        if article is None:
            logger.warning(f"PG Get by ID: статья {article_id} не найдена")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Статья с ID {article_id} не найдена"
            )
        
        logger.info(f"PG Get by ID: статья {article_id} получена")
        return ArticleOut(**article)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PG Get by ID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения из PostgreSQL: {str(e)}"
        )


@router.delete(
    "/articles/{article_id}",
    response_model=DeleteResponse,
    summary="Удалить статью из PostgreSQL"
)
async def delete_article_pg(
    request: Request,
    article_id: int
) -> DeleteResponse:
    """
    Удаление статьи из PostgreSQL
    
    Args:
        article_id: ID статьи
        
    Returns:
        Статус удаления
    """
    logger = request.app.state.logger
    db_manager = request.app.state.db_manager
    
    logger.info(f"PG Delete: article_id={article_id}")
    
    try:
        # Проверяем существование
        article = db_manager.get_article_by_id(article_id)
        if article is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Статья с ID {article_id} не найдена"
            )
        
        # Удаляем только из PostgreSQL
        with db_manager.pg_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM news WHERE id = %s", (article_id,))
            cur.close()
        
        logger.info(f"PG Delete: статья {article_id} удалена")
        
        return DeleteResponse(
            success=True,
            message=f"Статья {article_id} успешно удалена из PostgreSQL"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PG Delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления из PostgreSQL: {str(e)}"
        )
