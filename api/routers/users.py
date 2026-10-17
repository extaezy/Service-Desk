from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas import UserCreate, UserResponse
from db.queries import get_or_create_user_by_session


router = APIRouter(
    prefix="/users",
    tags=["users"]
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