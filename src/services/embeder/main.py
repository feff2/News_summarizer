import asyncio
import inspect
import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import torch
import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings
from sentence_transformers import SentenceTransformer

from .routers import encode_router
from .triton_client import TritonClient
from .triton_server import TritonServer
from ..shared.logger import LoggerWrapper


logger = LoggerWrapper("embeder_service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Lifespan: Инициализация Embeder клиента...")

    model = SentenceTransformer(settings.MODEL_NAME)

    encoder_client = LlmClient(
        inference_host=settings.INFERENCE_HOST,
        bi_encoder_port=settings.MODEL_PORT,
        inference_timeout_s=settings.INFERENCE_TIMEOUT,
        bi_encoder_name=settings.MODEL_NAME,
        device=settings.DEVICE
        logger=logger
    )
    encoder_client.create_model()
    

    encoder_client = LlmClient(
        inference_host=settings.INFERENCE_HOST,
        bi_encoder_port=settings.MODEL_PORT,
        inference_timeout_s=settings.INFERENCE_TIMEOUT,
        bi_encoder_name=settings.MODEL_NAME,
        device=settings.DEVICE
        logger=logger
    )
    encoder_client.create_model()
    
    app.state.encoder_client = encoder_client
    app.state.logger = logger
    logger.info("Lifespan: Embeder клиент успешно инициализирован.")

    yield  

    logger.info("Lifespan: Закрытие Embeder клиента...")
    app.state.llm_client.close()
    logger.info("Lifespan: Embeder клиент успешно закрыт.")


app = FastAPI(
    title="Embeder Service",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None,
    lifespan=lifespan,
)


app.include_router(generate_router, prefix=settings.API_V1_STR, tags=["Encode"])


@app.middleware("http")
async def generic_exception_handler(
    request: Request,
    call_next: Callable[..., Any],
) -> JSONResponse:
    try:
        return await call_next(request)
    except Exception as err:
        logger.exception(f"Unhandled exception for request {request.url.path}: {err}")
        return JSONResponse(
            content={"detail": "Internal Server Error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.services.embeder.main:app",
        host="0.0.0.0",
        port=settings.LLM_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        log_level="info",
    )
