# backend/app/api/chat.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from app.models import ChatRequest, ChatResponse, User
from app.api.dependencies import get_current_user  # Ensure correct import
from app.assistants.assistant import RAGAssistant
from app.firebase import get_firestore_client

import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/{chat_id}/message", tags=["Chat"])
async def post_message(
    chat_id: str,
    chat_in: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    firestore_client = get_firestore_client()
    chat_ref = firestore_client.collection('chats').document(chat_id)
    chat_doc = await asyncio.to_thread(chat_ref.get)
    if not chat_doc.exists:
        raise HTTPException(status_code=404, detail="Chat not found.")
    if chat_doc.to_dict().get('user_id') != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat.")

    assistant = RAGAssistant(
        chat_id=chat_id,
        firestore_client=firestore_client,
        user_id=current_user["uid"],
        user_name=current_user["username"]
    )
    await assistant.handle_message(chat_in.question)
    return {"message": "Message received. You can now connect to the stream."}

@router.get("/{chat_id}/stream", tags=["Chat"])
async def stream_response(
    chat_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    assistant = RAGAssistant.get_assistant(chat_id)
    if not assistant:
        raise HTTPException(status_code=400, detail="No message processing found for this chat.")
    sse_stream = await assistant.get_stream()
    return EventSourceResponse(sse_stream)