from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, admin, subscription, payment, download, profile, contact
from app.utils.logging_config import setup_logging, get_logger

# Setup enhanced logging with Rich
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info("[bold cyan]🚀 Starting Jarvis4Everyone Backend...[/bold cyan]")
    await connect_to_mongo()
    logger.info("[bold green]✓[/bold green] Application startup complete")
    yield
    # Shutdown
    logger.info("[bold yellow]⚠[/bold yellow] Shutting down application...")
    await close_mongo_connection()
    logger.info("[bold green]✓[/bold green] Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="Jarvis4Everyone - Subscription Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# Note: When allow_credentials=True, we cannot use wildcard "*" for origins
# Must explicitly list allowed origins
cors_origins = settings.cors_origins_list
logger.info(f"[cyan]🌐 CORS enabled for origins: {cors_origins}[/cyan]")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(subscription.router)
app.include_router(payment.router)
app.include_router(download.router)
app.include_router(contact.router)
logger.info("[bold green]✓[/bold green] All routers registered")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Jarvis4Everyone Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

