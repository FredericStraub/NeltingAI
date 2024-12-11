# backend/app/api/auth.py
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.models import UserOut, Token, UserIn
from app.firebase import get_auth_client, verify_firebase_id_token, get_firestore_client
from app.config import settings
import logging
from firebase_admin import firestore
from firebase_admin import auth as admin_auth  # Ensure Firebase Admin SDK is initialized
logger = logging.getLogger(__name__)

router = APIRouter()


# backend/app/api/auth.py

@router.post("/register", response_model=UserOut, tags=["Authentication"])
def register(user_in: UserIn, request: Request):
    try:
        firestore_client = get_firestore_client(request.app)
        # Create user in Firebase Authentication
        user = get_auth_client(request.app).create_user(
            email=user_in.email,
            password=user_in.password,
            display_name=user_in.username,  # Set display name as username
        )
        logger.info(f"User created with UID: {user.uid}")

        # Create corresponding Firestore User document
        user_doc_ref = firestore_client.collection('user').document(user.uid)
        user_doc_ref.set({
            "uid": user.uid,
            "username": user_in.username,
            "email": user_in.email,
            "created_at": firestore.SERVER_TIMESTAMP,
            "profile_picture": "",
            "bio": "",
            "last_active": firestore.SERVER_TIMESTAMP,
            "role": "user"
        })
        logger.info(f"Firestore User document created for UID: {user.uid}")

        # Generate custom token
        custom_token = get_auth_client(request.app).create_custom_token(user.uid)
        custom_token_str = custom_token.decode('utf-8')  # Decode bytes to string

        return UserOut(uid=user.uid, email=user.email, access_token=custom_token_str)
    except Exception as e:
        logger.exception(f"Registration failed: {e}")  # Use logger.exception for stack trace
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", tags=["Authentication"])
async def login(request: Request):
    """
    Endpoint to set the authentication token in an HTTP-only cookie.
    The client should provide the token in the request body or headers.
    """
    try:
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=400, detail="Authorization token missing")

        token = token.replace("Bearer ", "")
        # Optionally, verify the token here if necessary

        response = JSONResponse(content={"message": "Login successful"})
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=False,
            secure=False,  # Set to True if using HTTPS
            samesite="Strict",
            path="/"  # Adjust based on your requirements
        )
        return response
    except Exception as e:
        logger.exception(f"Login failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout", tags=["Authentication"])
def logout():
    """
    Logs out the user by clearing the access_token cookie.
    """
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie(key="access_token", path="/")
    return response