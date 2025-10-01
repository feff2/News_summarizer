import asyncio
import inspect
import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings

from .settings import settings
from .routers import get_info_guides_router
from ...shared.logger import LoggerWrapper


logger = LoggerWrapper("api_gateway")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Lifespan: API Gateway запускается...")
    app.state.logger = logger
    app.state.settings = settings
    yield
    logger.info("Lifespan: API Gateway останавливается...")


app = FastAPI(
    title="Api Gateway",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.include_router(get_info_guides_router, prefix=settings.API_V1_STR, tags=["Info Guides"])


@app.middleware("http")
async def generic_exception_handler(
    request: Request,
    call_next: Callable[..., Any],
) -> JSONResponse:
    try:
        return await call_next(request)
    except Exception as err:  # noqa: BLE001
        logger.exception(err)
        return JSONResponse(
            content={"detail": "Internal Server Error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.api_gateway.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        log_level="info",
    )