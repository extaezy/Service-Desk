from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas import (TicketCreate, TicketResponse, AdminTicketResponse,
                         TicketStatusResponse, TicketStatusUpdate)
from db.queries import (get_user_tickets_by_session, create_ticket_by_session, get_admin_tickets_by_session,
update_ticket_status_by_session)

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
)

@router.get(
    "/",
    response_model=list[TicketResponse]
)
async def get_tickets(
    telegram_user_id: int,
    session: AsyncSession = Depends(get_db)
):
    return await get_user_tickets_by_session(
        telegram_user_id,
        session
    )


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=201
)
async def add_ticket(
    data: TicketCreate,
    session: AsyncSession = Depends(get_db)
):
    try:
        ticket = await create_ticket_by_session(
            telegram_user_id=data.telegram_user_id,
            title=data.title,
            category=data.category,
            description=data.description,
            session=session
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc

    return ticket

@router.get(
    "/admin",
    response_model=list[AdminTicketResponse]
)
async def get_admin_tickets_route(
    status: str,
    session: AsyncSession = Depends(get_db)
):
    try:
        return await get_admin_tickets_by_session(
            status,
            session
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

@router.patch(
    "/{ticket_id}/status",
    response_model=TicketStatusResponse
)
async def update_ticket_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    session: AsyncSession = Depends(get_db)
):
    result = await update_ticket_status_by_session(
        ticket_id=ticket_id,
        status=data.status,
        session=session
    )

    if result is None:
        raise HTTPException(
            status_code=409,
            detail="Заявка не найдена или переход недопустим"
        )

    return result