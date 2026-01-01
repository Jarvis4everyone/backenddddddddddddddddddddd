from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
from app.models.user import PyObjectId


class Payment(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: Optional[PyObjectId] = None  # Optional because user might be deleted
    email: EmailStr  # Snapshot of user email at payment time
    plan_id: str = "monthly"
    amount: float
    currency: str = "INR"
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    status: Literal["pending", "completed", "failed", "refunded"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

