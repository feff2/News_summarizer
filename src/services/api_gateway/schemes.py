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

class RegisterUserIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    themes: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class LoginUserIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    user_id: str
    username: str
    themes: List[str]
    sources: List[str]


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserOut] = None