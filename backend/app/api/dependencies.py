# backend/app/api/dependencies.py

from fastapi import Request, Depends, HTTPException, status
from firebase_admin import auth
from app.firebase import get_auth_client, get_firestore_client
import logging

logger = logging.getLogger(__name__)

def verify_firebase_token(token: str, auth_client = Depends(get_auth_client)):
    """
    Verify Firebase ID token using the Auth client.
    """
    try:
        decoded_token = auth_client.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Error: {str(e)}"
        )

async def get_current_user(request: Request) -> dict:
    """
    Retrieve the current authenticated user from the request.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    auth_client = get_auth_client(request.app)
    try:
        decoded_token = auth_client.verify_id_token(token)
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    uid = decoded_token.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Fetch additional user information from Firestore
    firestore_client = get_firestore_client(request.app)
    user_doc = firestore_client.collection("user").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_data = user_doc.to_dict()
    full_user_data = {**decoded_token, **user_data}
    return full_user_data

async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Ensure that the current user has admin privileges.
    """
    try:
        role = current_user.get("role", "user")
        if role != "admin":
            logger.warning(f"User {current_user.get('uid')} attempted to access admin-only route.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    except Exception as e:
        logger.error(f"Error in admin role verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
