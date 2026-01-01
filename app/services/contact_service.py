from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.database import db
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class ContactService:
    @staticmethod
    async def create_contact(contact_data: dict, user_id: Optional[str] = None) -> dict:
        """Create a new contact submission"""
        if user_id:
            contact_data["user_id"] = ObjectId(user_id)
        contact_data["status"] = "new"
        contact_data["created_at"] = datetime.utcnow()
        contact_data["updated_at"] = datetime.utcnow()

        result = await db.database.contacts.insert_one(contact_data)
        contact = await db.database.contacts.find_one({"_id": result.inserted_id})
        contact["id"] = str(contact["_id"])
        del contact["_id"]
        if contact.get("user_id"):
            contact["user_id"] = str(contact["user_id"])
        return contact

    @staticmethod
    async def get_contact_by_id(contact_id: str) -> Optional[dict]:
        """Get contact by ID"""
        contact = await db.database.contacts.find_one({"_id": ObjectId(contact_id)})
        if contact:
            contact["id"] = str(contact["_id"])
            del contact["_id"]
            if contact.get("user_id"):
                contact["user_id"] = str(contact["user_id"])
        return contact

    @staticmethod
    async def get_all_contacts(
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[dict]:
        """Get all contacts (for admin)"""
        query = {}
        if status:
            query["status"] = status

        contacts = []
        async for contact in db.database.contacts.find(query).sort("created_at", -1).skip(skip).limit(limit):
            contact["id"] = str(contact["_id"])
            del contact["_id"]
            if contact.get("user_id"):
                contact["user_id"] = str(contact["user_id"])
            contacts.append(contact)
        return contacts

    @staticmethod
    async def update_contact_status(contact_id: str, status: str) -> Optional[dict]:
        """Update contact status"""
        result = await db.database.contacts.update_one(
            {"_id": ObjectId(contact_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )

        if result.modified_count:
            return await ContactService.get_contact_by_id(contact_id)
        return None

    @staticmethod
    async def delete_contact(contact_id: str) -> bool:
        """Delete contact"""
        result = await db.database.contacts.delete_one({"_id": ObjectId(contact_id)})
        return result.deleted_count > 0

