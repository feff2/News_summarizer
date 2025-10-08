import requests
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import List, Optional
from src.services.api_gateway.schemes import AuthResponse, LoginUserIn, UserOut, RegisterUserIn
router = APIRouter(tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    payload: RegisterUserIn
):
    settings = request.app.state.settings
    logger = request.app.state.logger
    
    try:
        check_resp = requests.get(
            f"{settings.DB_URL}/api/v1/pg/check_user",
            params={"username": payload.username}
        )
        
        if check_resp.status_code == 200 and check_resp.json().get("exists"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким никнеймом уже существует"
            )
        
        create_resp = requests.post(
            f"{settings.DB_URL}/api/v1/pg/create_user",
            json={
                "username": payload.username,
                "password": payload.password,
                "themes": payload.themes,
                "sources": payload.sources
            }
        )
        create_resp.raise_for_status()
        
        user_data = create_resp.json()
        
        logger.info(f"Пользователь {payload.username} успешно зарегистрирован")
        
        return AuthResponse(
            success=True,
            message="Регистрация прошла успешно",
            user=UserOut(
                user_id=user_data["user_id"],
                username=user_data["username"],
                themes=user_data.get("themes", []),
                sources=user_data.get("sources", [])
            )
        )
        
    except requests.RequestException as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации пользователя"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    payload: LoginUserIn
):
    settings = request.app.state.settings
    logger = request.app.state.logger
    
    try:
        auth_resp = requests.post(
            f"{settings.DB_URL}/api/v1/pg/authenticate",
            json={
                "username": payload.username,
                "password": payload.password
            }
        )
        
        if auth_resp.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный никнейм или пароль"
            )
        
        auth_resp.raise_for_status()
        user_data = auth_resp.json()
        
        logger.info(f"Пользователь {payload.username} успешно авторизован")
        
        return AuthResponse(
            success=True,
            message="Авторизация прошла успешно",
            user=UserOut(
                user_id=user_data["user_id"],
                username=user_data["username"],
                themes=user_data.get("themes", []),
                sources=user_data.get("sources", [])
            )
        )
        
    except HTTPException:
        raise
    except requests.RequestException as e:
        logger.error(f"Ошибка при авторизации пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при авторизации"
        )


@router.get("/check_username")
async def check_username(
    request: Request,
    username: str
):
    settings = request.app.state.settings
    
    try:
        check_resp = requests.get(
            f"{settings.DB_URL}/api/v1/pg/check_user",
            params={"username": username}
        )
        check_resp.raise_for_status()
        
        exists = check_resp.json().get("exists", False)
        
        return {
            "available": not exists,
            "message": "Никнейм свободен" if not exists else "Никнейм уже занят"
        }
        
    except requests.RequestException as e:
        request.app.state.logger.error(f"Ошибка при проверке никнейма: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при проверке никнейма"
        )


@router.get("/user/{user_id}", response_model=UserOut)
async def get_user(
    request: Request,
    user_id: str
):
    settings = request.app.state.settings
    
    try:
        user_resp = requests.get(
            f"{settings.DB_URL}/api/v1/pg/get_user_info",
            params={"user_id": user_id}
        )
        
        if user_resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        user_resp.raise_for_status()
        user_data = user_resp.json()
        
        return UserOut(
            user_id=user_data["user_id"],
            username=user_data["username"],
            themes=user_data.get("themes", []),
            sources=user_data.get("sources", [])
        )
        
    except HTTPException:
        raise
    except requests.RequestException as e:
        request.app.state.logger.error(f"Ошибка при получении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении информации о пользователе"
        )


@router.put("/user/{user_id}/preferences")
async def update_preferences(
    request: Request,
    user_id: str,
    themes: List[str] = [],
    sources: List[str] = []
):
    settings = request.app.state.settings
    
    try:
        update_resp = requests.put(
            f"{settings.DB_URL}/api/v1/pg/update_user_preferences",
            json={
                "user_id": user_id,
                "themes": themes,
                "sources": sources
            }
        )
        update_resp.raise_for_status()
        
        return {
            "success": True,
            "message": "Настройки успешно обновлены"
        }
        
    except requests.RequestException as e:
        request.app.state.logger.error(f"Ошибка при обновлении настроек: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении настроек"
        )