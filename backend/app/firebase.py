# backend/app/firebase.py

import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Path to your service account key
SERVICE_ACCOUNT_KEY_PATH = settings.SERVICE_ACCOUNT_KEY_PATH

# Initialize Firebase Admin
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(
            cred,
            {
                'storageBucket': settings.FIREBASE_STORAGE_BUCKET,
            }
        )
        logger.info("Firebase initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise e

# Firestore client
firestore_client = firestore.client()

# Storage bucket
storage_bucket = storage.bucket()

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
