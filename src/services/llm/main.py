from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.services.llm.llm_client import LlmClient
from src.services.llm.routers import generate_router
from src.services.llm.settings import settings
from src.shared.logger import LoggerWrapper

logger = LoggerWrapper("llm_service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Lifespan: Инициализация LLM клиента...")

    llm_client = LlmClient(
        model_name=settings.MODEL_NAME,
        device=settings.DEVICE,
        params=settings.PARAMS,
        system_prompt=settings.SYSTEM_PROMPT,
        logger=logger,
    )
    llm_client.start()
    app.state.llm_client = llm_client
    app.state.logger = logger
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
