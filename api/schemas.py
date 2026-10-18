from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

#Ticket work
class TicketCreate(BaseModel):
    telegram_user_id: int
    title: str = Field(min_length=1, max_length=100)
    category: Literal[
        "hardware", "software", "network", "other"
    ]
    description: str = Field(min_length=1, max_length=400)

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    category: str
    description: str
    status: str
    created_at: datetime

class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    telegram_user_id: int
    username: str | None
    full_name: str

#Full ticket information
class AdminTicketResponse(TicketResponse):
    user: UserInfo


#Update status
class TicketStatusUpdate(BaseModel):
    status: Literal['in_progress', 'closed']

class TicketStatusResponse(BaseModel):
    telegram_user_id: int
    status: str

#User work
class UserCreate(BaseModel):
    telegram_user_id: int
    username: str | None = None
    full_name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_user_id: int
    username: str | None
    full_name: str
    role: str
