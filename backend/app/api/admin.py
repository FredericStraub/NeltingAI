# backend/app/api/admin.py

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.api.dependencies import get_current_admin
from app.firebase import get_firestore_client
import logging
from models import AdminAssignRole
logger = logging.getLogger(__name__)

router = APIRouter()



@router.post("/assign-role", status_code=200, tags=["Admin"])
def assign_role(role_assignment: AdminAssignRole, current_admin: dict = Depends(get_current_admin)):
    firestore_client = get_firestore_client()
    user_ref = firestore_client.collection('user').document(role_assignment.uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        logger.error(f"Attempted to assign role to non-existent user: {role_assignment.uid}")
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"role": role_assignment.role})
    logger.info(f"User {role_assignment.uid} assigned role {role_assignment.role} by admin {current_admin.get('uid')}")
    return {"message": f"User {role_assignment.uid} assigned role {role_assignment.role} successfully."}