# backend/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.api import auth_router, chat_router, chat_create_router, upload_router, admin_router
from app.firebase import router as firebase_config_router  # Import the firebase router
from app.config import settings
import logging
import sys
from app.db import close_weaviate_client, get_weaviate_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="NeltingAI",
    description="An AI-driven application with authentication, chat, and upload functionalities.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOW_ORIGINS.split(',')],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Include API routers with appropriate prefixes and tags
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_create_router, prefix="/chat", tags=["Chat"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(firebase_config_router, tags=["Configuration"])  # Include Firebase Config Router

# Serve frontend static files
app.mount("/", StaticFiles(directory="/Volumes/External/Netling AI/frontend", html=True), name="frontend")

# Health Check Endpoint
@app.get('/health', tags=["Health Check"])
def health_check():
    return {'status': 'ok'}

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Startup Event to initialize resources
@app.on_event("startup")
async def startup_event():
    get_weaviate_client()
    logger.info("Application startup complete.")

# Shutdown Event to close Weaviate client (if necessary)
@app.on_event("shutdown")
async def shutdown_event():
    close_weaviate_client()
    logger.info("Application shutdown complete.")