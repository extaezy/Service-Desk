from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db, verify_api_key
from api.schemas import UserCreate, UserResponse
from db.queries import (
    get_or_create_user_by_session,
    is_admin_by_session,
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(verify_api_key)]
)


@router.post(
    "/",
    response_model=UserResponse
)
async def register_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_db)
):
    return await get_or_create_user_by_session(
        telegram_user_id=data.telegram_user_id,
        username=data.username,
        full_name=data.full_name,
        session=session
    )


@router.get("/{telegram_user_id}/is-admin")
async def check_admin(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_db)
):
    result = await is_admin_by_session(
        telegram_user_id=telegram_user_id,
        session=session
    )

    return {"is_admin": result}