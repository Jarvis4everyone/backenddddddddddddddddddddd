from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from app.services.subscription_service import SubscriptionService
from app.utils.subscription import is_subscription_active
from app.middleware.auth import get_current_user
from app.config import settings
from app.utils.logging_config import get_logger
import os

logger = get_logger(__name__)

router = APIRouter(prefix="/download", tags=["Download"])


def resolve_file_path(config_path: str) -> str:
    """Resolve file path, checking multiple possible locations"""
    # Get the project root directory (where run.py is located)
    # __file__ is app/routers/download.py, so we need to go up 2 levels to get to project root
    current_file_dir = os.path.dirname(os.path.abspath(__file__))  # app/routers
    routers_dir = os.path.dirname(current_file_dir)  # app
    project_root = os.path.dirname(routers_dir)  # Backend (project root)
    
    # Try absolute path first
    if os.path.isabs(config_path):
        if os.path.exists(config_path):
            return config_path
    
    # List of possible locations to check
    possible_paths = []
    
    # 1. Relative to project root (e.g., ./downloads or ./.downloads)
    project_relative = os.path.join(project_root, config_path.lstrip('./'))
    possible_paths.append(project_relative)
    
    # 2. In app folder (e.g., app/.downloads or app/downloads)
    app_folder = routers_dir  # app folder
    app_relative = os.path.join(app_folder, config_path.lstrip('./'))
    possible_paths.append(app_relative)
    
    # 3. Try with .downloads if downloads is in path
    if 'downloads' in config_path and not config_path.startswith('.'):
        hidden_path = config_path.replace('downloads', '.downloads')
        possible_paths.append(os.path.join(project_root, hidden_path.lstrip('./')))
        possible_paths.append(os.path.join(app_folder, hidden_path.lstrip('./')))
    
    # 4. Try original path as-is
    if os.path.exists(config_path):
        possible_paths.insert(0, os.path.abspath(config_path))
    
    # Check all possible paths
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
    
    # Return the first attempted path for error message
    return os.path.abspath(possible_paths[0] if possible_paths else config_path)


@router.get("/file")
async def download_file(current_user: dict = Depends(get_current_user)):
    """Download Jarvis4Everyone .zip file (requires active subscription)"""
    logger.info(f"[cyan]📥 Download request from user: {current_user['email']} (ID: {current_user['id']})[/cyan]")
    
    # Get user's subscription
    subscription = await SubscriptionService.get_user_subscription(current_user["id"])
    
    if not subscription:
        logger.warning(f"[yellow]⚠[/yellow] Download denied - No subscription for user: {current_user['email']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No subscription found. Please purchase a subscription to download."
        )
    
    # Check if subscription is active
    if not is_subscription_active(subscription):
        logger.warning(f"[yellow]⚠[/yellow] Download denied - Expired subscription for user: {current_user['email']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your subscription has expired. Please renew to download."
        )
    
    # Resolve file path
    file_path = resolve_file_path(settings.download_file_path)
    
    if not os.path.exists(file_path):
        # Get paths for better error message
        current_file = os.path.abspath(__file__)
        routers_dir = os.path.dirname(current_file)
        app_dir = os.path.dirname(routers_dir)
        project_root = os.path.dirname(app_dir)
        
        logger.error(f"[bold red]✗[/bold red] Download file not found at: [red]{file_path}[/red]")
        logger.debug(f"[yellow]📁[/yellow] Project root: {project_root}")
        logger.debug(f"[yellow]📁[/yellow] App folder: {app_dir}")
        logger.debug(f"[yellow]📁[/yellow] Config path: {settings.download_file_path}")
        logger.debug(f"[yellow]📁[/yellow] Checked locations:")
        logger.debug(f"  - {os.path.join(app_dir, settings.download_file_path.lstrip('./'))}")
        logger.debug(f"  - {os.path.join(app_dir, settings.download_file_path.replace('downloads', '.downloads').lstrip('./'))}")
        logger.debug(f"  - {os.path.join(project_root, settings.download_file_path.lstrip('./'))}")
        logger.debug(f"  - {os.path.join(project_root, settings.download_file_path.replace('downloads', '.downloads').lstrip('./'))}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Download file not available"
        )
    
    logger.info(f"[bold green]✓[/bold green] File download started for user: [cyan]{current_user['email']}[/cyan] (Path: {file_path})")
    
    # Return the file
    return FileResponse(
        path=file_path,
        filename="jarvis4everyone.zip",
        media_type="application/zip"
    )

