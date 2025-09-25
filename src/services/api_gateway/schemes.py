from typing import Optional, ClassVar, Dict, List

from pydantic import BaseModel, Field


class GetInfoGuidesIn(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    limit: int = Field(10, description="Количество инфоповодов")
    #На вырост: query: Optional[str] = Field(None, description="Дополнительный поиск по запросу")
    

class InfoGuide(BaseModel):
    title: str
    summary: str
    sources: List[str]  
    published_at: str

class GetInfoGuidesOut(BaseModel):
    guides: List[InfoGuide]

class AddNewSourceIn(BaseModel):
    user_id: str
    sources: List[str] = Field(..., description="Список RSS/ссылок/идентификаторов")

class AddNewSourceOut(BaseModel):
    added: List[str]
    skipped: List[str]

class UpdateUserProfileIn(BaseModel):
    user_id: str
    topics: Optional[List[str]] = None
    sources: Optional[List[str]] = None

class UpdateUserProfileOut(BaseModel):
    updated_topics: List[str]
    updated_sources: List[str]

