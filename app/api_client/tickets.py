from app.api_client.client import get_client


async def create_ticket(
    telegram_user_id: int,
    title: str,
    category: str,
    description: str,
):
    async with get_client() as client:
        response = await client.post(
            "/tickets/",
            json={
                "telegram_user_id": telegram_user_id,
                "title": title,
                "category": category,
                "description": description,
            }
        )

        response.raise_for_status()
        return response.json()


async def get_user_tickets(
    telegram_user_id: int
):
    async with get_client() as client:
        response = await client.get(
            "/tickets/",
            params={
                "telegram_user_id": telegram_user_id
            }
        )

        response.raise_for_status()
        return response.json()


async def get_admin_tickets(
    status: str,
    admin_id: int
):
    async with get_client() as client:
        response = await client.get(
            "/tickets/admin",
            params={"status": status},
            headers={
                "X-Telegram-User-Id": str(admin_id)
            }
        )
        print("HTTP статус:", response.status_code)
        print("Ответ FastAPI:", response.text)
        response.raise_for_status()
        return response.json()


async def update_ticket_status(
    ticket_id: int,
    status: str,
    admin_id: int
):
    async with get_client() as client:
        response = await client.patch(
            f"/tickets/{ticket_id}/status",
            json={"status": status},
            headers={
                "X-Telegram-User-Id": str(admin_id)
            }
        )

        response.raise_for_status()
        return response.json()