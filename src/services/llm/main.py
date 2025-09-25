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

from .llm_client import LlmClient
from .routers import generate_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Lifespan: Инициализация LLM клиента...")

    llm_client = LlmClient(
        model_name=settings.MODEL_NAME,
        device=torch.device(settings.DEVICE),
        params=settings.PARAMS,
        system_prompt=settings.SYSTEM_PROMPT,
    )
    llm_client.start()
    app.state.llm_client = llm_client
    logger.info("Lifespan: LLM клиент успешно инициализирован.")

    yield  

    logger.info("Lifespan: Закрытие LLM клиента...")
    app.state.llm_client.close()
    logger.info("Lifespan: LLM клиент успешно закрыт.")


app = FastAPI(
    title="LLM Service",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None,
    lifespan=lifespan,
)


app.include_router(generate_router, prefix=settings.API_V1_STR, tags=["Generation"])


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
        "src.services.llm.main:app",
        host="0.0.0.0",
        port=settings.LLM_PORT,
        workers=1,
        loop="uvloop",
        reload=settings.RELOAD,
        log_level="info",
    )
