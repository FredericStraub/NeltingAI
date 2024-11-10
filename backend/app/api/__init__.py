from .auth import router as auth_router
from .chat import router as chat_router
from .chat_create import router as chat_create_router  # Import the new router
from .upload import router as upload_router
from .admin import router as admin_router

# Optionally, include the new router with a prefix
app_routers = [
    auth_router,
    chat_router,
    chat_create_router,  # Add to included routers
    upload_router,
    admin_router
]
