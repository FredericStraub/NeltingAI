# backend/app/firebase.py

import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from app.config import settings
import logging
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

def initialize_firebase_app(app: FastAPI):
    """
    Initialize Firebase Admin SDK and store Firestore and Storage clients in app.state.
    """
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(
                cred,
                {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET,
                }
            )
            firestore_client = firestore.client()
            storage_bucket = storage.bucket()
            app.state.firestore_client = firestore_client
            app.state.storage_bucket = storage_bucket
            app.state.auth_client = auth
            logger.info("Firebase Admin initialized and clients stored in app.state.")
        else:
            logger.info("Firebase Admin already initialized.")
    except Exception as e:
        logger.exception(f"Failed to initialize Firebase Admin: {e}")
        raise e

def close_firebase_app(app: FastAPI):
    """
    Close the Firebase Admin SDK and clean up resources.
    """
    try:
        # Iterate over all initialized apps and delete them
        for app_name in list(firebase_admin._apps):
            firebase_admin.delete_app(firebase_admin.get_app(app_name))
            logger.info(f"Firebase app '{app_name}' deleted successfully.")
    except Exception as e:
        logger.exception(f"Failed to close Firebase Admin SDK: {e}")
        raise e

def get_firestore_client(app: FastAPI):
    """
    Retrieve Firestore client from app.state.
    """
    client = getattr(app.state, "firestore_client", None)
    if client is None:
        logger.error("Firestore client is not initialized.")
        raise RuntimeError("Firestore client is not initialized.")
    return client

def get_storage_bucket(app: FastAPI):
    """
    Retrieve Storage bucket from app.state.
    """
    bucket = getattr(app.state, "storage_bucket", None)
    if bucket is None:
        logger.error("Storage bucket is not initialized.")
        raise RuntimeError("Storage bucket is not initialized.")
    return bucket

def get_auth_client(app: FastAPI):
    """
    Retrieve Auth client from app.state.
    """
    auth_client = getattr(app.state, "auth_client", None)
    if auth_client is None:
        logger.error("Auth client is not initialized.")
        raise RuntimeError("Auth client is not initialized.")
    return auth_client

def verify_firebase_id_token(id_token: str, auth_client):
    """
    Verify Firebase ID token using the provided auth client.
    """
    try:
        decoded_token = auth_client.verify_id_token(id_token)
        uid = decoded_token['uid']
        return uid
    except Exception as e:
        logger.error(f"Failed to verify ID token: {e}")
        raise e

# Firebase configuration endpoint for frontend
router = APIRouter()

@router.get("/firebase-config", tags=["Configuration"])
def get_firebase_config():
    config = {
        "apiKey": settings.FRONTEND_FIREBASE_API_KEY,
        "authDomain": settings.FRONTEND_FIREBASE_AUTH_DOMAIN,
        "projectId": settings.FRONTEND_FIREBASE_PROJECT_ID,
        "storageBucket": settings.FRONTEND_FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": settings.FRONTEND_FIREBASE_MESSAGING_SENDER_ID,
        "appId": settings.FRONTEND_FIREBASE_APP_ID,
        "measurementId": settings.FRONTEND_FIREBASE_MEASUREMENT_ID
    }
    return JSONResponse(content=config)
