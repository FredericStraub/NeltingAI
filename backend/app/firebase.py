# backend/app/firebase.py

import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from app.config import settings
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(
                cred,
                {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET,
                }
            )
            logger.info("Firebase Admin initialized successfully.")
        except Exception as e:
            logger.exception(f"Failed to initialize Firebase Admin: {e}")
            raise e

# Call the initialization function at import time
initialize_firebase()

# Firestore client
firestore_client = firestore.client()

# Storage bucket
storage_bucket = storage.bucket()

# Define API Router for Firebase-related routes
router = APIRouter()

def get_firestore_client():
    return firestore_client

def get_storage_bucket():
    return storage_bucket

def get_auth_client():
    return auth

def verify_firebase_id_token(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return uid
    except Exception as e:
        logger.error(f"Failed to verify ID token: {e}")
        raise e

# Firebase configuration endpoint for frontend
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