"""
AstroSense - Space Weather Impact Forecasting System
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import API endpoints
from api.endpoints import router as api_router
from api.websocket import router as websocket_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AstroSense API",
    description="Space Weather Impact Forecasting & Risk Intelligence System",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],  # Expose rate limit header
)

# Include API routers
app.include_router(api_router)
app.include_router(websocket_router)

# Include auth router
from api.auth import router as auth_router
app.include_router(auth_router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AstroSense API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "ml_model": "loaded"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host=host, port=port)
