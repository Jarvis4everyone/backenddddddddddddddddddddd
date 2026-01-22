"""
Script to run the FastAPI application
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment variable (for Render deployment) or default to 8000
    # Always use port 8000 unless PORT environment variable is set (for Render)
    port = int(os.getenv("PORT", 8000))
    
    # Use 0.0.0.0 to bind to all interfaces - works for both local and production
    # Accessible via localhost, 127.0.0.1, or the machine's IP address
    host = "0.0.0.0"
    
    # Only enable reload in development (when PORT is not set)
    reload = not bool(os.getenv("PORT"))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )

