from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class PaymentResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    email: str
    plan_id: str
    amount: float
    currency: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    status: Literal["pending", "completed", "failed", "refunded"]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    amount: float
    currency: str = "INR"


class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

