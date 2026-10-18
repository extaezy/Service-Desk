import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session
from db.queries import is_admin_by_session

load_dotenv()

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")


async def get_db():
    async with async_session() as session:
        yield session


async def verify_api_key(
    x_api_key: str | None = Header(default=None)
):
    if not SERVICE_API_KEY:
        raise RuntimeError("SERVICE_API_KEY не настроен")

    if not x_api_key or not secrets.compare_digest(
        x_api_key,
        SERVICE_API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный API-ключ"
        )

async def require_admin(
    x_telegram_user_id: int = Header(),
    session: AsyncSession = Depends(get_db)
):
    is_admin = await is_admin_by_session(
        telegram_user_id=x_telegram_user_id,
        session=session
    )

    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав администратора"
        )