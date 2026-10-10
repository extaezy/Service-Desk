from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, update

from db.database import async_session
from db.models import User, Ticket
from sqlalchemy.orm import selectinload

async def get_or_create_user(
    telegram_user_id: int,
    username: str | None,
    full_name: str,
) -> User:

    async with async_session() as session:
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
    description: str,
) -> Ticket:

    async with async_session() as session:
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
    if status not in ("new", "in_progress"):
        raise ValueError("Недопустимый статус заявки")

    async with async_session() as session:
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

async def get_telegram_id(user_id: int) -> int | None:
    async with async_session() as session:
        stmt = select(User.telegram_user_id).where(
            User.id == user_id
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()