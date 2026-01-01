from fastapi import APIRouter, Depends, HTTPException, status, Response
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.utils.security import create_access_token, create_refresh_token
from app.middleware.auth import get_refresh_token_from_cookie
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    logger.info(f"[cyan]📝 Registration attempt for email: {user_data.email}[/cyan]")
    
    # Check if user already exists
    existing_user = await UserService.get_user_by_email(user_data.email)
    if existing_user:
        logger.warning(f"[yellow]⚠[/yellow] Registration failed - Email already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_dict = user_data.model_dump()
    user = await UserService.create_user(user_dict)
    logger.info(f"[bold green]✓[/bold green] User registered successfully: [cyan]{user_data.email}[/cyan] (ID: {user['id']})")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, response: Response):
    """Login user and return access token, set refresh token in cookie"""
    logger.info(f"[cyan]🔐 Login attempt for email: {user_data.email}[/cyan]")
    
    # Verify credentials
    user = await UserService.verify_user(user_data.email, user_data.password)
    if not user:
        logger.warning(f"[yellow]⚠[/yellow] Login failed - Invalid credentials for: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user["id"]})
    refresh_token = create_refresh_token(data={"sub": user["id"]})
    
    # Store refresh token in database
    await AuthService.store_refresh_token(user["id"], refresh_token)
    
    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,  # Use secure in production
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )
    
    admin_status = "[bold magenta]ADMIN[/bold magenta]" if user.get("is_admin") else "User"
    logger.info(f"[bold green]✓[/bold green] Login successful: {admin_status} [cyan]{user_data.email}[/cyan] (ID: {user['id']})")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str = Depends(get_refresh_token_from_cookie)
):
    """Refresh access token using refresh token from cookie"""
    logger.debug("[cyan]🔄 Token refresh attempt[/cyan]")
    result = await AuthService.refresh_access_token(refresh_token)
    if not result:
        logger.warning("[yellow]⚠[/yellow] Token refresh failed - Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    logger.debug("[bold green]✓[/bold green] Token refreshed successfully")
    return result

