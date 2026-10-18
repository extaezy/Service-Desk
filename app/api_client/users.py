from app.api_client.client import get_client


async def register_user(
    telegram_user_id: int,
    username: str | None,
    full_name: str,
):
    async with get_client() as client:
        response = await client.post(
            "/users/",
            json={
                "telegram_user_id": telegram_user_id,
                "username": username,
                "full_name": full_name,
            }
        )

        response.raise_for_status()
        return response.json()


async def is_admin(telegram_user_id: int) -> bool:
    async with get_client() as client:
        response = await client.get(
            f"/users/{telegram_user_id}/is-admin"
        )

        response.raise_for_status()
        return response.json()["is_admin"]