# backend/app/api/documents.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models import DocumentOut  # Ensure this Pydantic model is defined appropriately
from app.api.dependencies import get_current_user  # Authentication dependency
from app.firebase import get_firestore_client
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/documents", response_model=List[DocumentOut], tags=["Documents"])
async def get_documents(current_user: dict = Depends(get_current_user)):
    """
    Fetch a list of documents with metadata from Firestore.
    """
    firestore_client = get_firestore_client()
    if not firestore_client:
        logger.error("Firestore client is not initialized.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        )
    
    try:
        # Fetch all documents from Firestore 'documents' collection for the current user
        docs = await asyncio.to_thread(lambda: firestore_client.collection("documents").where("user_id", "==", current_user.get("uid")).stream())
        documents = []
        for doc in docs:
            doc_data = doc.to_dict()
            documents.append(DocumentOut(
                id=doc.id,
                description=doc_data.get("description"),
                file_name=doc_data.get("file_name"),
                file_type=doc_data.get("file_type"),
                file_url=doc_data.get("file_url"),
                size=doc_data.get("size"),
                upload_id=doc_data.get("upload_id"),
                uploaded_at=doc_data.get("uploaded_at"),
                user_id=doc_data.get("user_id")
            ))
        logger.info(f"Fetched {len(documents)} documents for user UID: {current_user.get('uid')}")
        return documents
    except Exception as e:
        logger.exception(f"Failed to fetch documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch documents.",
        )

@router.get("/documents/sources", response_model=List[str], tags=["Documents"])
async def get_unique_sources(current_user: dict = Depends(get_current_user)):
    """
    Fetch a list of unique sources from Firestore documents for the current user.
    """
    firestore_client = get_firestore_client()
    if not firestore_client:
        logger.error("Firestore client is not initialized.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        )
    
    try:
        # Fetch all documents from Firestore 'documents' collection for the current user
        docs = await asyncio.to_thread(lambda: firestore_client.collection("documents").where("user_id", "==", current_user.get("uid")).stream())
        sources = set()
        for doc in docs:
            doc_data = doc.to_dict()
            source = doc_data.get("source")
            if source:
                sources.add(source)
        unique_sources = list(sources)
        logger.info(f"Fetched {len(unique_sources)} unique sources for user UID: {current_user.get('uid')}")
        return unique_sources
    except Exception as e:
        logger.exception(f"Failed to fetch unique sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch sources.",
        )