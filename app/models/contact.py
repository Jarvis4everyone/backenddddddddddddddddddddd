from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
from app.models.user import PyObjectId


class Contact(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    subject: str
    message: str
    status: Literal["new", "read", "replied", "archived"] = "new"
    user_id: Optional[PyObjectId] = None  # Optional - user might not be logged in
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

