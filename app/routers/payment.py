from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.payment import PaymentCreate, PaymentVerify, PaymentResponse
from app.services.payment_service import PaymentService
from app.services.subscription_service import SubscriptionService
from app.middleware.auth import get_current_user
from app.config import settings
from app.utils.logging_config import get_logger
import json

logger = get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-order", response_model=dict)
async def create_payment_order(
    payment_data: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create Razorpay order for payment
    
    Request body: { "amount": <number in rupees>, "currency": "INR" }
    Response: { "order_id": "...", "amount": <paise>, "currency": "INR", "key_id": "...", "payment_id": "..." }
    """
    try:
        logger.info(
            f"[cyan]💳[/cyan] Creating payment order for user: {current_user['email']}, "
            f"amount: {payment_data.amount} {payment_data.currency}"
        )
        
        # Validate amount
        if payment_data.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0"
            )
        
        # Validate currency
        if payment_data.currency.upper() != "INR":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only INR currency is supported"
            )
        
        # Create Razorpay order with retry logic
        order = await PaymentService.create_order(payment_data.amount, payment_data.currency)
        
        # Create payment record
        payment = await PaymentService.create_payment_record(
            current_user["id"],
            current_user["email"],
            payment_data.amount,
            payment_data.currency,
            order["id"]
        )
        
        logger.info(
            f"[bold green]✓[/bold green] Payment order created successfully: "
            f"order_id={order['id']}, payment_id={payment['id']}"
        )
        
        # Return exact format as specified in requirements
        return {
            "order_id": order["id"],
            "amount": order["amount"],  # Already in paise from Razorpay
            "currency": order["currency"],
            "key_id": settings.razorpay_key_id,
            "payment_id": payment["id"]
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.error(f"[bold red]✗[/bold red] Invalid payment request: [red]{str(e)}[/red]")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConnectionError as e:
        logger.error(f"[bold red]✗[/bold red] Connection error: [red]{str(e)}[/red]")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable. Please try again in a moment."
        )
    except Exception as e:
        logger.error(f"[bold red]✗[/bold red] Unexpected error: [red]{str(e)}[/red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment order. Please try again."
        )


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    verify_data: PaymentVerify,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify Razorpay payment and activate subscription
    
    Request body: {
        "razorpay_order_id": "...",
        "razorpay_payment_id": "...",
        "razorpay_signature": "..."
    }
    
    After successful verification:
    - Updates payment status to "completed"
    - Activates subscription (1 month) for the current user
    """
    logger.info(
        f"[cyan]🔐[/cyan] Verifying payment for user: {current_user['email']}, "
        f"order_id: {verify_data.razorpay_order_id}"
    )
    
    # Get payment record
    payment = await PaymentService.get_payment_by_order_id(verify_data.razorpay_order_id)
    if not payment:
        logger.warning(
            f"[yellow]⚠[/yellow] Payment record not found for order_id: {verify_data.razorpay_order_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )
    
    # Verify payment belongs to current user
    if str(payment.get("user_id")) != current_user["id"]:
        logger.warning(
            f"[yellow]⚠[/yellow] Payment ownership mismatch: "
            f"payment.user_id={payment.get('user_id')}, current_user.id={current_user['id']}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payment does not belong to current user"
        )
    
    # Verify payment signature
    is_valid = await PaymentService.verify_payment(
        verify_data.razorpay_order_id,
        verify_data.razorpay_payment_id,
        verify_data.razorpay_signature
    )
    
    if not is_valid:
        logger.error(
            f"[bold red]✗[/bold red] Invalid payment signature for order_id: {verify_data.razorpay_order_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    # Update payment status to completed
    payment = await PaymentService.update_payment_status(
        verify_data.razorpay_order_id,
        verify_data.razorpay_payment_id,
        verify_data.razorpay_signature,
        "completed"
    )
    
    # Activate subscription (1 month)
    logger.info(f"[cyan]📅[/cyan] Activating subscription for user: {current_user['email']}")
    subscription = await SubscriptionService.renew_subscription(current_user["id"], 1)
    logger.info(
        f"[bold green]✓[/bold green] Payment verified and subscription activated: "
        f"subscription_id={subscription.get('id')}, end_date={subscription.get('end_date')}"
    )
    
    return payment


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook (for payment status updates)"""
    # Get webhook signature from headers
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook signature"
        )
    
    # Get request body
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Verify webhook signature
    is_valid = await PaymentService.verify_webhook_signature(body_str, signature)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse webhook payload
    try:
        payload = json.loads(body_str)
        event = payload.get("event")
        
        if event == "payment.captured":
            # Payment successful
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_data.get("order_id")
            
            if order_id:
                payment = await PaymentService.get_payment_by_order_id(order_id)
                if payment and payment["status"] == "pending":
                    await PaymentService.update_payment_status(
                        order_id,
                        payment_data.get("id", ""),
                        signature,
                        "completed"
                    )
                    
                    # Activate subscription if user exists
                    if payment.get("user_id"):
                        await SubscriptionService.renew_subscription(str(payment["user_id"]), 1)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"[bold red]✗[/bold red] Webhook processing error: [red]{str(e)}[/red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )

