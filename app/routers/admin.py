from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.user import UserResponse, UserCreate, UserUpdate, PasswordReset, UserWithSubscriptionResponse
from app.schemas.subscription import SubscriptionResponse, SubscriptionCreate, SubscriptionExtend
from app.schemas.payment import PaymentResponse
from app.services.user_service import UserService
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService
from app.middleware.auth import get_current_admin
from app.utils.logging_config import get_logger
from app.utils.subscription import is_subscription_active

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# User Management
@router.get("/users", response_model=List[UserWithSubscriptionResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all users with subscription information (admin only)"""
    logger.info(f"[cyan]👥 Admin {current_admin['email']} requested users list (skip={skip}, limit={limit})[/cyan]")
    
    users = await UserService.get_all_users(skip=skip, limit=limit)
    
    # Enhance each user with subscription information
    enhanced_users = []
    for user in users:
        subscription = await SubscriptionService.get_user_subscription(user["id"])
        
        user_data = {
            **user,
            "subscription": subscription,
            "has_subscription": subscription is not None,
            "has_active_subscription": False
        }
        
        if subscription:
            user_data["has_active_subscription"] = is_subscription_active(subscription)
        
        enhanced_users.append(user_data)
    
    logger.info(f"[bold green]✓[/bold green] Returned {len(enhanced_users)} users with subscription info")
    return enhanced_users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Get user by ID (admin only)"""
    user = await UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new user (admin only)"""
    existing_user = await UserService.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = user_data.model_dump()
    user = await UserService.create_user(user_dict)
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update user (admin only)"""
    update_dict = user_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Check email uniqueness if updating email
    if "email" in update_dict:
        existing_user = await UserService.get_user_by_email(update_dict["email"])
        if existing_user and existing_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    user = await UserService.update_user(user_id, update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_user_password(
    user_id: str,
    password_data: PasswordReset,
    current_admin: dict = Depends(get_current_admin)
):
    """Reset user password (admin only) - logs user out everywhere"""
    success = await UserService.reset_password(user_id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "Password reset successfully. User logged out everywhere."}


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete user (admin only) - keeps payments with email snapshot"""
    if user_id == current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = await UserService.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}


# Subscription Management
@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def get_all_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all subscriptions (admin only)"""
    subscriptions = await SubscriptionService.get_all_subscriptions(skip=skip, limit=limit)
    return subscriptions


@router.post("/subscriptions/activate", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def activate_subscription(
    subscription_data: SubscriptionCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Activate subscription without payment (admin only)"""
    subscription = await SubscriptionService.activate_without_payment(
        subscription_data.user_id,
        subscription_data.months
    )
    return subscription


@router.post("/subscriptions/{user_id}/extend", response_model=SubscriptionResponse)
async def extend_subscription(
    user_id: str,
    extend_data: SubscriptionExtend,
    current_admin: dict = Depends(get_current_admin)
):
    """Extend user subscription (admin only)"""
    subscription = await SubscriptionService.extend_subscription(user_id, extend_data.months)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active subscription not found"
        )
    return subscription


@router.post("/subscriptions/{user_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Cancel user subscription (admin only)"""
    success = await SubscriptionService.cancel_subscription(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active subscription not found"
        )
    return {"message": "Subscription cancelled successfully"}


# Payment Viewing
@router.get("/payments", response_model=List[PaymentResponse])
async def get_all_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all payments (admin only)"""
    payments = await PaymentService.get_all_payments(skip=skip, limit=limit)
    return payments

