from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    status: Literal["active", "expired", "cancelled"]
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    user_id: str
    months: int = 1  # Number of months to add


class SubscriptionExtend(BaseModel):
    months: int = 1


class SubscriptionRenew(BaseModel):
    months: int = 1

