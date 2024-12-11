# backend/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.security import OAuth2PasswordBearer
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
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.documents import router as documents_router
from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from app.api import (
    auth_router,
    chat_router,
    chat_create_router,
    upload_router,
    admin_router,
    documents_router
)
from app.firebase import initialize_firebase_app, close_firebase_app
from app.db import (
    initialize_weaviate_client,
    ensure_weaviate_schema,
    test_weaviate_connection,
    close_weaviate_client
)
from app.config import settings
import logging
import sys
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "Authorization" in request.headers:
            logger.debug(f"Authorization Header: {request.headers['Authorization']}")
        response = await call_next(request)
        return response

# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Startup logic
        initialize_firebase_app(app)
        logger.info("Firebase initialized.")
        
        initialize_weaviate_client(app)
        logger.info("Weaviate client initialized.")
        
        ensure_weaviate_schema(app)
        logger.info("Weaviate schema ensured.")
        
        test_weaviate_connection(app)
        logger.info("Weaviate connection tested.")
        
        logger.info("Application startup complete.")
        
        yield  # Application runs here
        
    except Exception as e:
        logger.exception(f"Error during startup: {e}")
        sys.exit(1)  # Exit the application if startup fails
        
    finally:
        # Shutdown logic
        close_weaviate_client(app)
        logger.info("Weaviate client closed.")
        
        close_firebase_app(app)
        logger.info("Firebase Admin SDK closed.")
        
        logger.info("Application shutdown complete.")

# Initialize FastAPI application with lifespan
app = FastAPI(
    title="NeltingAI",
    description="An AI-driven application with authentication, chat, and upload functionalities.",
    version="1.0.0.",
    lifespan=lifespan  # Pass the lifespan context manager here
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOW_ORIGINS.split(',')],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers with appropriate prefixes and tags
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_create_router, prefix="/chat", tags=["Chat"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(firebase_config_router, tags=["Configuration"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])  # Include Documents Router
app.add_middleware(DebugMiddleware)


# Serve frontend static files with SPA fallback
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pathlib import Path
import os

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 404 and not path.startswith("api"):
            index_path = os.path.join(self.directory, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
        return response

# Define the frontend directory using pathlib for better path handling
frontend_dir = Path("/Volumes/External/Netling AI/frontend")

# Verify that the directory exists
if not frontend_dir.is_dir():
    logger.error(f"Frontend directory does not exist: {frontend_dir}")
    sys.exit(1)

# Mount static files using the custom SPAStaticFiles class
app.mount("/", SPAStaticFiles(directory=str(frontend_dir), html=True), name="frontend")

# Health Check Endpoint
@app.get('/health', tags=["Health Check"])
def health_check():
    return {'status': 'ok'}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@app.get("/secure-endpoint")
def secure_endpoint(token: str = Depends(oauth2_scheme)):
    return {"message": "This endpoint is secured!", "token": token}

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
