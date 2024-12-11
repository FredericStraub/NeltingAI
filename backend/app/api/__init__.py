from .auth import router as auth_router
from .chat import router as chat_router
from .chat_create import router as chat_create_router
from .upload import router as upload_router
from .admin import router as admin_router
from .documents import router as documents_router  # Importing documents_router

# Define all app routers in a list for easy inclusion
app_routers = [
    auth_router,
    chat_router,
    chat_create_router,
    upload_router,
    admin_router,
    documents_router  # Including documents_router in the list
]
