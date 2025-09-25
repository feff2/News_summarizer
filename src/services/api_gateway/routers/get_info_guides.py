from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from ..logger import api_logger
from ..schemes import GetInfoGuidesIn, InfoGuide, GetInfoGuidesOut
from ..settings import settings


router = APIRouter(tags=["info_guides"], include_in_schema=False)


async def __info_guides(
    user_id: str,
    limit: int,
) -> GetInfoGuidesOut:
    filter_resp = requests.post(f"{settings.POSTGRES_API}/get_user_info", json={"user_id": user_id})
    filter_resp.raise_for_status()
    themes, sources = filter_resp.json()["filters"], filter_resp.json()["sources"]

    info_guides_resp = requests.post(f"{settings.QDRANT_API}/get_candidates", json={"themes": themes, "sources": sources, "limit": limit})
    info_guides_resp.raise_for_status()

    info_guides = []

    for info in info_guides_resp:
        info_guides.append(
            InfoGuide(
                title=info.title, 
                summary=info.summary,
                sources=info.sources
            )
        )

    return GetInfoGuidesOut(guides=info_guides)


@router.get("/info_guides", response_model=StatOut)
async def info_guides(
    request: GetInfoGuidesIn,
):
    return await __info_guides(GetInfoGuidesIn.user_id, GetInfoGuidesIn.limit)