from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.subscription import SubscriptionResponse, SubscriptionRenew
from app.services.subscription_service import SubscriptionService
from app.middleware.auth import get_current_user
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription"""
    subscription = await SubscriptionService.get_user_subscription(current_user["id"])
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    return subscription


@router.post("/renew", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def renew_subscription(
    renew_data: SubscriptionRenew,
    current_user: dict = Depends(get_current_user)
):
    """Renew subscription (can renew after expiry)"""
    subscription = await SubscriptionService.renew_subscription(
        current_user["id"],
        renew_data.months
    )
    return subscription


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """Cancel current user's subscription"""
    success = await SubscriptionService.cancel_subscription(current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active subscription not found"
        )
    return {"message": "Subscription cancelled successfully"}

