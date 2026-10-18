import os
import httpx

from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8000"
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")


def get_client() -> httpx.AsyncClient:
    if not SERVICE_API_KEY:
        raise RuntimeError("SERVICE_API_KEY не настроен")

    return httpx.AsyncClient(
        base_url=API_URL,
        timeout=10.0,
        headers={"X-API-Key": SERVICE_API_KEY},
    )
