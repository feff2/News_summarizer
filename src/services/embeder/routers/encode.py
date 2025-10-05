from fastapi import APIRouter, Request


from src. services.embeder.schemes import EncodeIn, EncodeOut


router = APIRouter(tags=["encode", "bi_encoder"], include_in_schema=False)


async def __encode(
    request: Request,
    input_: EncodeIn,
) -> EncodeOut:
    logger = request.app.state.logger
    client = request.app.state.encoder_client

    msg = f"Encode request_id={input_.request_id}, text={input_.text[:100]}"
    logger.debug(msg)

    vectors = await client.encode(
        input_.request_id,
        input_.text,
    )

    msg = f"Vectors request_id={vectors}"
    logger.debug(msg)

    return EncodeOut(
        request_id=input_.request_id,
        vectors=vectors,
    )

@router.post(
    f"/encode/",
    summary="Получить вектор текста",
)
async def predict(request: Request, input_: EncodeIn) -> EncodeOut:
    return await __encode(request, input_)