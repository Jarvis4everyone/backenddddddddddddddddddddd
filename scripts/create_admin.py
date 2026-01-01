"""
Script to create an admin user in the database
Run: python scripts/create_admin.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import connect_to_mongo, close_mongo_connection, db
from app.utils.security import get_password_hash
from app.services.user_service import UserService


async def create_admin():
    """Create admin user"""
    await connect_to_mongo()
    
    print("Creating admin user...")
    print("Enter admin details:")
    name = input("Name: ")
    email = input("Email: ")
    contact_number = input("Contact Number: ")
    password = input("Password: ")
    
    # Check if user already exists
    existing_user = await UserService.get_user_by_email(email)
    if existing_user:
        print(f"User with email {email} already exists!")
        await close_mongo_connection()
        return
    
    # Create admin user
    user_data = {
        "name": name,
        "email": email,
        "contact_number": contact_number,
        "password": password,
        "is_admin": True
    }
    
    user = await UserService.create_user(user_data)
    print(f"Admin user created successfully!")
    print(f"User ID: {user['id']}")
    print(f"Email: {user['email']}")
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_admin())

