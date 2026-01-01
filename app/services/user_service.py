from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.database import db
from app.models.user import User
from app.utils.security import get_password_hash, verify_password
from app.utils.subscription import check_subscription_expiry
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class UserService:
    @staticmethod
    async def create_user(user_data: dict) -> dict:
        """Create a new user"""
        user_data["password_hash"] = get_password_hash(user_data.pop("password"))
        # Ensure is_admin is set (default to False if not provided)
        # This field is ALWAYS stored in the database
        if "is_admin" not in user_data:
            user_data["is_admin"] = False
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        
        result = await db.database.users.insert_one(user_data)
        user = await db.database.users.find_one({"_id": result.inserted_id})
        user["id"] = str(user["_id"])
        del user["_id"]
        del user["password_hash"]
        # Ensure is_admin is in the response (should always be present now)
        if "is_admin" not in user:
            user["is_admin"] = False
        return user
    
    @staticmethod
    async def ensure_is_admin_field():
        """Migration: Ensure all users have is_admin field set (defaults to False)"""
        result = await db.database.users.update_many(
            {"is_admin": {"$exists": False}},
            {"$set": {"is_admin": False}}
        )
        if result.modified_count > 0:
            logger.info(f"[yellow]⚠[/yellow] Updated {result.modified_count} users to set is_admin=False")
        return result.modified_count

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[dict]:
        """Get user by email"""
        user = await db.database.users.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
            # Ensure is_admin is in the response
            if "is_admin" not in user:
                user["is_admin"] = False
            return user
        return None

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[dict]:
        """Get user by ID"""
        user = await db.database.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
            # Ensure is_admin is in the response
            if "is_admin" not in user:
                user["is_admin"] = False
            return user
        return None

    @staticmethod
    async def verify_user(email: str, password: str) -> Optional[dict]:
        """Verify user credentials"""
        user = await db.database.users.find_one({"email": email})
        if not user:
            return None
        
        if not verify_password(password, user["password_hash"]):
            return None
        
        # Update last login
        await db.database.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Check subscription expiry on login
        subscription = await db.database.subscriptions.find_one(
            {"user_id": user["_id"], "status": "active"}
        )
        if subscription and check_subscription_expiry(subscription):
            await db.database.subscriptions.update_one(
                {"_id": subscription["_id"]},
                {"$set": {"status": "expired", "updated_at": datetime.utcnow()}}
            )
        
        user["id"] = str(user["_id"])
        del user["_id"]
        # Ensure is_admin is in the response
        if "is_admin" not in user:
            user["is_admin"] = False
        return user

    @staticmethod
    async def get_all_users(skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all users (for admin)"""
        users = []
        async for user in db.database.users.find().skip(skip).limit(limit):
            user["id"] = str(user["_id"])
            del user["_id"]
            del user["password_hash"]
            # Ensure is_admin is in the response
            if "is_admin" not in user:
                user["is_admin"] = False
            users.append(user)
        return users

    @staticmethod
    async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
        """Update user"""
        update_data["updated_at"] = datetime.utcnow()
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await UserService.get_user_by_id(user_id)
        return None

    @staticmethod
    async def reset_password(user_id: str, new_password: str) -> bool:
        """Reset user password and invalidate all refresh tokens"""
        password_hash = get_password_hash(new_password)
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": password_hash, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count:
            # Delete all refresh tokens for this user (logout everywhere)
            await db.database.refresh_tokens.delete_many({"user_id": ObjectId(user_id)})
            return True
        return False

    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """Delete user, subscriptions, and refresh tokens. Keep payments with email snapshot."""
        user = await UserService.get_user_by_id(user_id)
        if not user:
            return False
        
        # Delete user
        await db.database.users.delete_one({"_id": ObjectId(user_id)})
        
        # Delete subscriptions
        await db.database.subscriptions.delete_many({"user_id": ObjectId(user_id)})
        
        # Delete refresh tokens
        await db.database.refresh_tokens.delete_many({"user_id": ObjectId(user_id)})
        
        # Payments are kept with email snapshot (user_id is already optional)
        return True

