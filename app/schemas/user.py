from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.schemas.subscription import SubscriptionResponse


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    contact_number: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithSubscriptionResponse(BaseModel):
    """User response with subscription information for admin panel"""
    id: str
    name: str
    email: EmailStr
    contact_number: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    subscription: Optional[SubscriptionResponse] = None
    has_subscription: bool = False
    has_active_subscription: bool = False

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    contact_number: str
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = None
    is_admin: Optional[bool] = None


class PasswordReset(BaseModel):
    new_password: str

