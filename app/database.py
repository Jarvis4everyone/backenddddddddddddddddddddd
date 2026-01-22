from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def connect_to_mongo():
    """Create database connection"""
    try:
        logger.info(f"[cyan]📦 Connecting to MongoDB: {settings.database_name}...[/cyan]")
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.database = db.client[settings.database_name]
        logger.info(f"[bold green]✓[/bold green] Connected to MongoDB database: [cyan]{settings.database_name}[/cyan]")
        
        # Create indexes
        await create_indexes()
    except Exception as e:
        logger.error(f"[bold red]✗[/bold red] Failed to connect to MongoDB: [red]{str(e)}[/red]")
        raise


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("[yellow]📦[/yellow] MongoDB connection closed")


async def create_indexes():
    """Create database indexes for performance"""
    try:
        logger.debug("[cyan]🔍 Creating database indexes...[/cyan]")

        # User indexes
        await db.database.users.create_index("email", unique=True)
        await db.database.users.create_index("created_at")

        # Subscription indexes
        await db.database.subscriptions.create_index("user_id")
        await db.database.subscriptions.create_index("status")
        await db.database.subscriptions.create_index("end_date")

        # Payment indexes
        await db.database.payments.create_index("user_id")
        await db.database.payments.create_index("razorpay_order_id", unique=True)
        
        # Fix razorpay_payment_id index: make it sparse to allow multiple null values
        # Drop existing index if it exists (to update from non-sparse to sparse)
        try:
            await db.database.payments.drop_index("razorpay_payment_id_1")
            logger.debug("[yellow]⚠[/yellow] Dropped old razorpay_payment_id index")
        except Exception:
            # Index doesn't exist or has different name, that's okay
            pass
        
        # Create sparse unique index: only indexes non-null values, allows multiple nulls
        await db.database.payments.create_index("razorpay_payment_id", unique=True, sparse=True)
        
        await db.database.payments.create_index("email")
        await db.database.payments.create_index("created_at")

        # Refresh token indexes
        await db.database.refresh_tokens.create_index("user_id")
        await db.database.refresh_tokens.create_index("token", unique=True)
        await db.database.refresh_tokens.create_index("expires_at")

        # Contact indexes
        await db.database.contacts.create_index("email")
        await db.database.contacts.create_index("status")
        await db.database.contacts.create_index("user_id")
        await db.database.contacts.create_index("created_at")

        logger.info("[bold green]✓[/bold green] Database indexes created successfully")
        
        # Ensure all users have is_admin field (migration)
        from app.services.user_service import UserService
        await UserService.ensure_is_admin_field()
        
    except Exception as e:
        logger.error(f"[bold red]✗[/bold red] Error creating indexes: [red]{str(e)}[/red]")

