from sqlalchemy.exc import SQLAlchemyError

from db.database import async_session
from db.models import Ticket


async def create_ticket(
    telegram_user_id: int,
    title: str,
    category: str,
    description: str,
) -> Ticket:
    async with async_session() as session:
        try:
            ticket = Ticket(
                telegram_user_id=telegram_user_id,
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