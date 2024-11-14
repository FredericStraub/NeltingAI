# backend/app/api/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.firebase import verify_firebase_id_token, get_firestore_client
from app.models import User  # Now defined
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        uid = verify_firebase_id_token(token)
        firestore_client = get_firestore_client()
        user_doc = firestore_client.collection('user').document(uid).get()
        if not user_doc.exists:
            logger.warning(f"User document not found for UID: {uid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_data = user_doc.to_dict()
        user = User(
            uid=uid,
            email=user_data.get('email', ''),
            username=user_data.get('username', '')
            # Populate other fields if available
        )
        return user
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.username != 'admin':  # Adjust based on your admin identification logic
        logger.warning(f"User {current_user.uid} attempted to access admin-only route.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user