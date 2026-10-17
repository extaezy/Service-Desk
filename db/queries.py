from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, update

from api.schemas import TicketCreate
from db.database import async_session
from db.models import User, Ticket
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

async def get_or_create_user(
    telegram_user_id: int,
    username: str | None,
    full_name: str,
) -> User:

    async with async_session() as session:
        return await get_or_create_user_by_session(
            telegram_user_id=telegram_user_id,
            username=username,
            full_name=full_name,
            session=session
        )

async def get_or_create_user_by_session(
    telegram_user_id: int,
    username: str | None,
    full_name: str,
    session: AsyncSession
) -> User:

    try:
        stmt = select(User).where(
            User.telegram_user_id == telegram_user_id
        )

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                full_name=full_name,
            )
            session.add(user)

        else:
            user.username = username
            user.full_name = full_name

        await session.commit()
        await session.refresh(user)

        return user

    except SQLAlchemyError:
        await session.rollback()
        raise

async def get_user_tickets(
    telegram_user_id: int,
) -> list[Ticket]:
    async with async_session() as session:
        return await get_user_tickets_by_session(
            telegram_user_id,
            session
        )

async def get_user_tickets_by_session(
    telegram_user_id: int,
    session: AsyncSession
) -> list[Ticket]:
    stmt = (
        select(Ticket)
        .join(User, Ticket.user_id == User.id)
        .where(
            User.telegram_user_id == telegram_user_id,
            Ticket.status != "closed"
        )
        .order_by(
            Ticket.created_at.desc(),
            Ticket.id.desc()
        )
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())

async def create_ticket(
    telegram_user_id: int,
    title: str,
    category: str,
    description: str
) -> Ticket:
    async with async_session() as session:
        return await create_ticket_by_session(
            telegram_user_id = telegram_user_id,
            title = title,
            category = category,
            description = description,
            session = session
        )

async def create_ticket_by_session(
    telegram_user_id: int,
    title: str,
    category: str,
    description: str,
    session: AsyncSession
) -> Ticket:

    try:
        stmt = select(User).where(
            User.telegram_user_id == telegram_user_id
        )

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError(
                "Пользователь не зарегистрирован"
            )

        ticket = Ticket(
            user_id=user.id,
            title=title,
            category=category,
            description=description,
        )

        session.add(ticket)

        await session.commit()
        await session.refresh(ticket)

        return ticket

    except SQLAlchemyError:
        await session.rollback()
        raise


async def is_admin(telegram_user_id: int) -> bool:
    async with async_session() as session:
        stmt = select(User.role).where(
            User.telegram_user_id == telegram_user_id
        )

        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        return role == "admin"

async def get_admin_tickets(status: str) -> list[Ticket]:
    async with async_session() as session:
        return await get_admin_tickets_by_session(
            status = status,
            session = session,
        )

async def get_admin_tickets_by_session(
        status: str,
        session: AsyncSession
) -> list[Ticket]:
    if status not in ("new", "in_progress"):
        raise ValueError("Недопустимый статус заявки")

    stmt = (
        select(Ticket)
        .options(selectinload(Ticket.user))
        .where(Ticket.status == status)
        .order_by(
            Ticket.created_at.asc(),
            Ticket.id.asc()
        )
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())

async def take_ticket(ticket_id: int) -> int | None:
    async with async_session() as session:
        return await take_ticket_by_session(
            ticket_id=ticket_id,
            session=session
        )

async def take_ticket_by_session(
    ticket_id: int,
    session: AsyncSession
) -> int | None:
    stmt = (
        update(Ticket)
        .where(
            Ticket.id == ticket_id,
            Ticket.status == "new"
        )
        .values(status="in_progress")
        .returning(Ticket.user_id)
    )

    result = await session.execute(stmt)
    user_id = result.scalar_one_or_none()

    await session.commit()

    return user_id

async def close_ticket(ticket_id: int) -> int | None:
    async with async_session() as session:
        return await close_ticket_by_session(
            ticket_id=ticket_id,
            session=session
        )

async def close_ticket_by_session(
    ticket_id: int,
    session: AsyncSession
) -> int | None:
    stmt = (
        update(Ticket)
        .where(
            Ticket.id == ticket_id,
            Ticket.status == "in_progress"
        )
        .values(status="closed")
        .returning(Ticket.user_id)
    )

    result = await session.execute(stmt)
    user_id = result.scalar_one_or_none()

    await session.commit()

    return user_id

async def update_ticket_status_by_session(
    ticket_id: int,
    status: str,
    session: AsyncSession
) -> dict | None:

    if status == "in_progress":
        old_status = "new"
    elif status == "closed":
        old_status = "in_progress"
    else:
        raise ValueError("Недопустимый статус")

    try:
        stmt = (
            update(Ticket)
            .where(
                Ticket.id == ticket_id,
                Ticket.status == old_status
            )
            .values(status=status)
            .returning(Ticket.user_id)
        )

        result = await session.execute(stmt)
        user_id = result.scalar_one_or_none()

        if user_id is None:
            await session.rollback()
            return None

        stmt = select(User.telegram_user_id).where(
            User.id == user_id
        )

        result = await session.execute(stmt)
        telegram_user_id = result.scalar_one_or_none()

        if telegram_user_id is None:
            await session.rollback()
            return None

        await session.commit()

        return {
            "telegram_user_id": telegram_user_id,
            "status": status
        }

    except SQLAlchemyError:
        await session.rollback()
        raise

async def get_telegram_id(user_id: int) -> int | None:
    async with async_session() as session:
        stmt = select(User.telegram_user_id).where(
            User.id == user_id
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()