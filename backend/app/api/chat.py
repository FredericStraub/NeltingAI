# backend/app/api/chat.py

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from app.models import ChatRequest, ChatResponse, User
from app.api.dependencies import get_current_user  # Ensure correct import
from app.assistants.assistant import RAGAssistant
from app.firebase import get_firestore_client

import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/{chat_id}", tags=["Chat"])
async def chat(
    chat_id: str, 
    chat_in: ChatRequest, 
    current_user: User = Depends(get_current_user),
):
    try:
        firestore_client = get_firestore_client()
        # Verify that the chat_id exists and belongs to the user
        chat_ref = firestore_client.collection('chats').document(chat_id)
        chat_doc = await asyncio.to_thread(chat_ref.get)  # Make Firestore call asynchronous
        if not chat_doc.exists:
            logger.warning(f"Chat ID {chat_id} does not exist.")
            raise HTTPException(status_code=404, detail="Chat not found.")
        if chat_doc.to_dict().get('user_id') != current_user["uid"]:
            logger.warning(f"User {current_user.uid} attempted to access chat {chat_id} not owned by them.")
            raise HTTPException(status_code=403, detail="Not authorized to access this chat.")
        
        assistant = RAGAssistant(
            chat_id=chat_id, 
            firestore_client=firestore_client, 
            user_id=current_user["uid"],
            user_name=current_user["username"]
        )
        sse_stream = await assistant.run(message=chat_in.question)  # Await the asynchronous run method
        return EventSourceResponse(sse_stream)
    except Exception as e:
        logger.exception(f"Error in chat endpoint: {e}")  # Logs stack trace
        raise HTTPException(status_code=500, detail=str(e))