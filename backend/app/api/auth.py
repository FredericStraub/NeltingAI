# backend/app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.models import UserOut, Token
from app.firebase import get_auth_client, verify_firebase_id_token, get_firestore_client
from app.config import settings
import logging
from firebase_admin import firestore

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic Models
class UserIn(BaseModel):
    email: str
    password: str
    username: str  # Added username field

class UserOut(BaseModel):
    uid: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Initialize OAuth2PasswordBearer to expect token in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def verify_firebase_token(token: str = Depends(oauth2_scheme)):
    try:
        uid = verify_firebase_id_token(token)
        return uid
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=UserOut, tags=["Authentication"])
def register(user_in: UserIn):
    try:
        # Create user in Firebase Authentication
        user = get_auth_client().create_user(
            email=user_in.email,
            password=user_in.password,
            display_name=user_in.username  # Set display name as username
        )
        logger.info(f"User created with UID: {user.uid}")

        # Create corresponding Firestore User document
        firestore_client = get_firestore_client()
        user_doc_ref = firestore_client.collection('user').document(user.uid)  # Using 'user' collection
        user_doc_ref.set({
            "username": user_in.username,
            "email": user_in.email,
            "created_at": firestore.SERVER_TIMESTAMP,
            "profile_picture": "",  # Default empty or provide a default URL
            "bio": "",
            "last_active": firestore.SERVER_TIMESTAMP
        })
        logger.info(f"Firestore User document created for UID: {user.uid}")

        return UserOut(uid=user.uid, email=user.email)
    except Exception as e:
        logger.exception(f"Registration failed: {e}")  # Use logger.exception for stack trace
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token, tags=["Authentication"])
def login(credentials: UserIn):
    try:
        # Firebase Admin SDK does not handle password verification.
        # Typically, password verification is handled on the client-side using Firebase Client SDK.
        # After client-side verification, the client obtains a JWT (ID token) and sends it to the backend.
        # Here, we'll simulate token retrieval for demonstration purposes.

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Login endpoint not implemented. Use Firebase Client SDK for authentication.",
        )
    except Exception as e:
        logger.exception(f"Login failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
