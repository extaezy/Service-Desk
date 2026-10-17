from fastapi import FastAPI

from api.routers.tickets import router as tickets_router
from api.routers.users import router as users_router

app = FastAPI()

app.include_router(tickets_router)
app.include_router(users_router)