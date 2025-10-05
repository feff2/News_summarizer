from fastapi import APIRouter

from fastapi import APIRouter, Request
from src.services.llm.schemes import GenerateIn, GenerateOut

router = APIRouter(tags=["generate", "llm"], include_in_schema=False)

async def __generate(
    request: Request,
    input_: GenerateIn,
) -> GenerateOut:
    logger = request.app.state.logger
    llm_service = request.app.state.llm_service

    msg = f"Generate request_id={input_.request_id}, context={input_.context[:100]}"
    logger.debug(msg)

    generated = await llm_service.generate(
        input_.request_id,
        input_.context,
        input_.prompt,
        input_.system_prompt,
        input_.max_new_tokens,
        input_.params,
    )

    msg = f"Requested reques_id={generated}"
    logger.debug(msg)

    return GenerateOut(
        request_id=input_.request_id,
        response=generated,
    )

@router.post(
    f"/generate/",
    summary="Получить ответ",
)
async def predict(request: Request, input_: GenerateIn) -> GenerateOut:
    return await __generate(request, input_)