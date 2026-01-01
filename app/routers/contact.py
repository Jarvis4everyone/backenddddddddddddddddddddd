from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from app.services.contact_service import ContactService
from app.middleware.auth import get_current_admin
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/contact", tags=["Contact"])

# Optional authentication for contact submission
security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    try:
        from app.utils.security import verify_token
        from app.services.user_service import UserService
        
        token = credentials.credentials
        payload = verify_token(token, "access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await UserService.get_user_by_id(user_id)
        return user
    except Exception:
        return None


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact(
    contact_data: ContactCreate,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Submit a contact form (public endpoint - authentication optional)
    If user is logged in, their user_id will be associated with the contact
    """
    logger.info(f"[cyan]📧 Contact form submission from: {contact_data.email}[/cyan]")
    
    contact_dict = contact_data.model_dump()
    user_id = current_user["id"] if current_user else None
    
    contact = await ContactService.create_contact(contact_dict, user_id)
    
    logger.info(f"[bold green]✓[/bold green] Contact submission created (ID: {contact['id']})")
    return contact


@router.get("/admin/all", response_model=List[ContactResponse])
async def get_all_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, regex="^(new|read|replied|archived)$"),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all contact submissions (admin only)"""
    logger.info(f"[cyan]📋 Admin {current_admin['email']} requested contacts list (skip={skip}, limit={limit}, status={status})[/cyan]")
    
    contacts = await ContactService.get_all_contacts(skip=skip, limit=limit, status=status)
    
    logger.info(f"[bold green]✓[/bold green] Returned {len(contacts)} contacts")
    return contacts


@router.get("/admin/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Get contact by ID (admin only)"""
    logger.info(f"[cyan]👁️ Admin {current_admin['email']} requested contact: {contact_id}[/cyan]")
    
    contact = await ContactService.get_contact_by_id(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact


@router.patch("/admin/{contact_id}/status", response_model=ContactResponse)
async def update_contact_status(
    contact_id: str,
    status_data: ContactUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update contact status (admin only)"""
    logger.info(f"[cyan]✏️ Admin {current_admin['email']} updating contact {contact_id} status to: {status_data.status}[/cyan]")
    
    contact = await ContactService.update_contact_status(contact_id, status_data.status)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    logger.info(f"[bold green]✓[/bold green] Contact status updated successfully")
    return contact


@router.delete("/admin/{contact_id}", status_code=status.HTTP_200_OK)
async def delete_contact(
    contact_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete contact (admin only)"""
    logger.info(f"[cyan]🗑️ Admin {current_admin['email']} deleting contact: {contact_id}[/cyan]")
    
    success = await ContactService.delete_contact(contact_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    logger.info(f"[bold green]✓[/bold green] Contact deleted successfully")
    return {"message": "Contact deleted successfully"}

