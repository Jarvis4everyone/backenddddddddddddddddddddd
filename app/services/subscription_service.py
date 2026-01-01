from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from app.database import db
from app.utils.subscription import calculate_end_date
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class SubscriptionService:
    @staticmethod
    async def create_subscription(user_id: str, months: int = 1, start_date: Optional[datetime] = None) -> dict:
        """Create a new subscription"""
        if start_date is None:
            start_date = datetime.utcnow()
        
        end_date = calculate_end_date(start_date, months)
        
        subscription = {
            "user_id": ObjectId(user_id),
            "plan_id": "monthly",
            "status": "active",
            "start_date": start_date,
            "end_date": end_date,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.database.subscriptions.insert_one(subscription)
        subscription = await db.database.subscriptions.find_one({"_id": result.inserted_id})
        subscription["id"] = str(subscription["_id"])
        del subscription["_id"]  # Remove ObjectId _id field
        subscription["user_id"] = str(subscription["user_id"])
        return subscription

    @staticmethod
    async def get_user_subscription(user_id: str) -> Optional[dict]:
        """Get active subscription for user"""
        subscription = await db.database.subscriptions.find_one(
            {"user_id": ObjectId(user_id), "status": {"$in": ["active", "expired"]}},
            sort=[("created_at", -1)]
        )
        if subscription:
            subscription["id"] = str(subscription["_id"])
            del subscription["_id"]  # Remove ObjectId _id field
            subscription["user_id"] = str(subscription["user_id"])
        return subscription

    @staticmethod
    async def extend_subscription(user_id: str, months: int) -> Optional[dict]:
        """Extend existing subscription"""
        subscription = await db.database.subscriptions.find_one(
            {"user_id": ObjectId(user_id), "status": "active"}
        )
        
        if not subscription:
            return None
        
        current_end_date = subscription["end_date"]
        if isinstance(current_end_date, str):
            current_end_date = datetime.fromisoformat(current_end_date.replace("Z", "+00:00"))
        
        new_end_date = calculate_end_date(current_end_date, months)
        
        await db.database.subscriptions.update_one(
            {"_id": subscription["_id"]},
            {"$set": {
                "end_date": new_end_date,
                "updated_at": datetime.utcnow()
            }}
        )
        
        subscription = await db.database.subscriptions.find_one({"_id": subscription["_id"]})
        subscription["id"] = str(subscription["_id"])
        del subscription["_id"]  # Remove ObjectId _id field
        subscription["user_id"] = str(subscription["user_id"])
        return subscription

    @staticmethod
    async def renew_subscription(user_id: str, months: int) -> dict:
        """Renew subscription (can renew after expiry)"""
        # Cancel any existing subscriptions
        await db.database.subscriptions.update_many(
            {"user_id": ObjectId(user_id), "status": {"$in": ["active", "expired"]}},
            {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )
        
        # Create new subscription
        return await SubscriptionService.create_subscription(user_id, months)

    @staticmethod
    async def cancel_subscription(user_id: str) -> bool:
        """Cancel subscription"""
        result = await db.database.subscriptions.update_many(
            {"user_id": ObjectId(user_id), "status": "active"},
            {"$set": {
                "status": "cancelled",
                "cancelled_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_all_subscriptions(skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all subscriptions (for admin)"""
        subscriptions = []
        async for sub in db.database.subscriptions.find().skip(skip).limit(limit):
            sub["id"] = str(sub["_id"])
            del sub["_id"]  # Remove ObjectId _id field
            sub["user_id"] = str(sub["user_id"])
            subscriptions.append(sub)
        return subscriptions

    @staticmethod
    async def activate_without_payment(user_id: str, months: int) -> dict:
        """Admin can activate subscription without payment"""
        # Cancel any existing subscriptions
        await db.database.subscriptions.update_many(
            {"user_id": ObjectId(user_id), "status": {"$in": ["active", "expired"]}},
            {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )
        
        # Create new active subscription
        return await SubscriptionService.create_subscription(user_id, months)

