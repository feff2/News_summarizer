from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.services.db.routers import qd_router, pg_router
from src.services.db.db_manager import DatabaseManager
from src.shared.logger import LoggerWrapper
from src.services.db.settings import settings

logger = LoggerWrapper("db_service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Lifespan: Инициализация DB Manager...")

    db_manager = DatabaseManager(
        pg_config=settings.PG_CONFIG,
        qdrant_host=settings.QDRANT_HOST,
        qdrant_port=settings.QDRANT_PORT,
        collection_name=settings.COLLECTION_NAME,
    )

    db_manager.get_qdrant_client()
    logger.info("Qdrant client успешно инициализирован.")
    db_manager.pg_connection()
    logger.info("Postgress client успешно инициализирован.")

    app.state.db_manager = db_manager
    app.state.logger = logger
    logger.info("Lifespan: DB Manager успешно инициализирован.")

    yield  

    logger.info("Lifespan: Закрытие DB Manager...")
    db_manager.close()
    logger.info("Lifespan: DB Manager успешно закрыт.")


app = FastAPI(
    title="DB Service",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None,
    lifespan=lifespan,
)


app.include_router(qd_router,  prefix=settings.API_V1_STR, tags=["QD"])
app.include_router(pg_router, prefix=settings.API_V1_STR, tags=["PG"])



@app.middleware("http")
async def generic_exception_handler(
    request: Request,
    call_next: Callable[..., Any],
) -> JSONResponse:
    try:
        return await call_next(request)
    except Exception as err:
        logger.error(f"Unhandled exception for request {request.url.path}: {err}")
        return JSONResponse(
            content={"detail": "Internal Server Error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.services.db.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        log_level="info",
    )
