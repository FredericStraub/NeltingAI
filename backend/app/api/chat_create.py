# backend/app/api/chat_create.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.firebase import get_firestore_client
from app.api.auth import verify_firebase_token
from uuid import uuid4
from datetime import datetime, timezone
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

class NewChatResponse(BaseModel):
    chat_id: str

@router.post("/new", response_model=NewChatResponse, tags=["Chat"])
async def create_new_chat(
    uid: str = Depends(verify_firebase_token),  # Correct dependency
    payload: Optional[dict] = None  # Make payload optional
):
    """
    Endpoint to create a new chat. Generates a unique chat_id and initializes the chat document in Firestore.
    """
    firestore_client = get_firestore_client()
    chat_id = f"chat_{uuid4().hex}"
    chat_ref = firestore_client.collection('chats').document(chat_id)
    
    try:
        await asyncio.to_thread(chat_ref.set, {
            'user_id': uid,
            'created_at': datetime.now(timezone.utc),
            'messages': []
        })
        logger.info(f"New chat created with chat_id: {chat_id} for user_id: {uid}")
        return NewChatResponse(chat_id=chat_id)
    except Exception as e:
        logger.exception(f"Failed to create new chat for user_id {uid}: {e}")  # Use logger.exception for stack trace
        raise HTTPException(status_code=500, detail="Failed to create new chat.")