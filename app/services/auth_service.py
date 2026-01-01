from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId
from app.database import db
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class AuthService:
    @staticmethod
    async def store_refresh_token(user_id: str, token: str) -> None:
        """Store refresh token in database"""
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        refresh_token = {
            "user_id": ObjectId(user_id),
            "token": token,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        await db.database.refresh_tokens.insert_one(refresh_token)

    @staticmethod
    async def get_refresh_token(token: str) -> Optional[dict]:
        """Get refresh token from database"""
        refresh_token = await db.database.refresh_tokens.find_one({"token": token})
        if refresh_token:
            # Check if expired
            expires_at = refresh_token.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            
            if datetime.utcnow() > expires_at:
                await db.database.refresh_tokens.delete_one({"_id": refresh_token["_id"]})
                return None
            
            refresh_token["id"] = str(refresh_token["_id"])
            refresh_token["user_id"] = str(refresh_token["user_id"])
        return refresh_token

    @staticmethod
    async def delete_refresh_token(token: str) -> bool:
        """Delete refresh token"""
        result = await db.database.refresh_tokens.delete_one({"token": token})
        return result.deleted_count > 0

    @staticmethod
    async def delete_all_user_tokens(user_id: str) -> None:
        """Delete all refresh tokens for a user"""
        await db.database.refresh_tokens.delete_many({"user_id": ObjectId(user_id)})

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[dict]:
        """Generate new access token from refresh token"""
        # Verify token
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # Check if token exists in database
        token_record = await AuthService.get_refresh_token(refresh_token)
        if not token_record:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Create new access token
        access_token = create_access_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

