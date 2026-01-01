from datetime import datetime, timedelta


def check_subscription_expiry(subscription: dict) -> bool:
    """Check if subscription has expired and return True if expired"""
    if subscription.get("status") == "cancelled":
        return False
    
    end_date = subscription.get("end_date")
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    elif isinstance(end_date, datetime):
        pass
    else:
        return True
    
    return datetime.utcnow() > end_date


def is_subscription_active(subscription: dict) -> bool:
    """Check if subscription is currently active"""
    if subscription.get("status") != "active":
        return False
    
    return not check_subscription_expiry(subscription)


def calculate_end_date(start_date: datetime, months: int) -> datetime:
    """Calculate subscription end date by adding months"""
    # Simple month addition (30 days per month)
    days = months * 30
    return start_date + timedelta(days=days)

