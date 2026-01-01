from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.subscription import SubscriptionResponse
from app.services.user_service import UserService
from app.services.subscription_service import SubscriptionService
from app.middleware.auth import get_current_user
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    logger.info(f"[cyan]👤 Profile request from user: {current_user['email']} (ID: {current_user['id']})[/cyan]")
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile (name, contact_number only)"""
    logger.info(f"[cyan]✏️ Profile update request from user: {current_user['email']}[/cyan]")
    
    # Only allow updating name and contact_number for regular users
    # Email and is_admin cannot be changed by user themselves
    update_dict = user_data.model_dump(exclude_unset=True)
    
    # Remove fields that users cannot update themselves
    update_dict.pop("email", None)
    update_dict.pop("is_admin", None)
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    user = await UserService.update_user(current_user["id"], update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"[bold green]✓[/bold green] Profile updated successfully for user: [cyan]{current_user['email']}[/cyan]")
    return user


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_my_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status"""
    logger.info(f"[cyan]📋 Subscription status request from user: {current_user['email']}[/cyan]")
    
    subscription = await SubscriptionService.get_user_subscription(current_user["id"])
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    return subscription


@router.get("/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """Get complete dashboard data (profile + subscription)"""
    logger.info(f"[cyan]📊 Dashboard data request from user: {current_user['email']}[/cyan]")
    
    # Get subscription
    subscription = await SubscriptionService.get_user_subscription(current_user["id"])
    
    # Prepare dashboard data
    dashboard_data = {
        "user": current_user,
        "subscription": subscription,
        "has_active_subscription": False
    }
    
    if subscription:
        from app.utils.subscription import is_subscription_active
        dashboard_data["has_active_subscription"] = is_subscription_active(subscription)
    
    return dashboard_data

