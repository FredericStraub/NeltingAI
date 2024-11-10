# backend/app/api/admin.py

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.firebase import get_firestore_client, verify_firebase_id_token
from fastapi.security import OAuth2PasswordBearer
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Ensure logging is configured

router = APIRouter()

class AdminAssignRole(BaseModel):
    uid: str
    role: str  # Expected to be "admin"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # Ensure tokenUrl is correct

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        uid = verify_firebase_id_token(token)
    except Exception as e:
        logger.error(f"Token verification failed for admin access: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    firestore_client = get_firestore_client()
    user_doc = firestore_client.collection('user').document(uid).get()  # Ensure 'user' collection is used
    if not user_doc.exists:
        logger.warning(f"Admin role assignment failed: User {uid} not found.")
        raise HTTPException(status_code=404, detail="User not found")
    user_data = user_doc.to_dict()
    if user_data.get('role') != 'admin':
        logger.warning(f"User {uid} attempted to assign admin roles without proper authorization.")
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    return uid

@router.post("/assign-role", status_code=200, tags=["Admin"])
def assign_role(role_assignment: AdminAssignRole, admin_uid: str = Depends(get_current_admin)):
    firestore_client = get_firestore_client()
    user_ref = firestore_client.collection('user').document(role_assignment.uid)  # Ensure 'user' collection is used
    user_doc = user_ref.get()
    if not user_doc.exists:
        logger.error(f"Attempted to assign role to non-existent user: {role_assignment.uid}")
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"role": role_assignment.role})
    logger.info(f"User {role_assignment.uid} assigned role {role_assignment.role} by admin {admin_uid}")
    return {"message": f"User {role_assignment.uid} assigned role {role_assignment.role} successfully."}
