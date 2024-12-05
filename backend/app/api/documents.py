# backend/app/api/documents.py

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List
from app.models import DocumentOut  # Ensure this Pydantic model is defined appropriately
from app.api.dependencies import get_current_user, get_current_admin # Authentication dependency
from app.firebase import get_firestore_client, get_storage_bucket
from app.db import get_weaviate_client
from urllib.parse import urlparse
from urllib.parse import urlparse, unquote
from weaviate import Client
import logging
import asyncio
from weaviate.classes.query import Filter

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

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documents"])
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a document and its associated data.
    """
    firestore_client = get_firestore_client()
    storage_bucket = get_storage_bucket()
    weaviate_client = get_weaviate_client()

    if not firestore_client or not storage_bucket or not weaviate_client:
        logger.error("One or more services are not initialized.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        )

    try:
        # Get the document from Firestore
        doc_ref = firestore_client.collection("documents").document(document_id)
        doc_snapshot = await asyncio.to_thread(doc_ref.get)

        if not doc_snapshot.exists:
            logger.warning(f"Document {document_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        doc_data = doc_snapshot.to_dict()

        # Check if the current user is the owner
        if doc_data.get("user_id") != current_user.get("uid"):
            logger.warning(f"User {current_user.get('uid')} attempted to delete a document they do not own.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this document.")
        upload_id = doc_data.get("upload_id")
        if upload_id:
            try:
                # Construct the filter for deleting objects
                collection = weaviate_client.collections.get("ChatDocument")
                collection.data.delete_many(
                    where=Filter.by_property("upload_id").contains_any([upload_id])
                )
                logger.info(f"Deleted vectors from Weaviate for upload_id: {upload_id}")
            except Exception as e:
                logger.error(f"Failed to delete vectors from Weaviate: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete vectors from Weaviate: {e}",
                )
            logger.info(f"Deleted vectors from Weaviate for upload_id: {upload_id}")

        # Delete the file from Firebase Storage
        file_url = doc_data.get("file_url")
        if file_url:
            # Extract the blob path from the file URL
            parsed_url = urlparse(file_url)

            # Extract the path and decode it
            blob_path = parsed_url.path.lstrip('/')
            blob_path = unquote(blob_path)

            # Ensure the blob path does not include the bucket name
            bucket_name = storage_bucket.name
            if blob_path.startswith(f"{bucket_name}/"):
                blob_path = blob_path[len(f"{bucket_name}/"):]

            logger.debug(f"Final blob path: {blob_path}")

            # Now, blob_path should be ready for deletion
            blob = storage_bucket.blob(blob_path)
            await asyncio.to_thread(blob.delete)
            logger.info(f"Deleted file from Firebase Storage: {blob_path}")

        

        # Delete the document from Firestore
        await asyncio.to_thread(doc_ref.delete)
        logger.info(f"Deleted document {document_id} from Firestore.")

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        logger.exception(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document.",
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