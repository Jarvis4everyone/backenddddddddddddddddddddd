from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Literal


class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


class ContactResponse(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    message: str
    status: Literal["new", "read", "replied", "archived"]
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactUpdate(BaseModel):
    status: Literal["new", "read", "replied", "archived"]

