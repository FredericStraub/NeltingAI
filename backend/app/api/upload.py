# backend/app/api/upload.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
import os
import aiofiles
import logging
from datetime import timedelta, datetime
import asyncio
from app.api.dependencies import get_current_admin  # Assuming only admins can upload
from app.loader import ingest_and_index
from app.config import settings
from app.firebase import get_storage_bucket, get_firestore_client
from uuid import uuid4

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/upload-file/", status_code=201, tags=["Upload"])
async def upload_file(
    description: str = Form(...),  # New field for document description
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_current_admin),  # Only admins can upload
):
    logger.debug(f"Received request to upload file: {file.filename}")
    try:
        cleaned_filename = file.filename.strip()
        if not (cleaned_filename.endswith(".pdf") or cleaned_filename.endswith(".docx")):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only PDF and DOCX are supported.",
            )

        # Log admin user details
        logger.debug(f"Admin user details: {admin_user}")

        # Define the storage path in Firebase Storage
        storage_bucket = get_storage_bucket()
        blob_path = f"uploads/{admin_user.get('uid')}/{cleaned_filename}"
        blob = storage_bucket.blob(blob_path)
        logger.debug(f"Firebase blob path: {blob_path}")

        # Define upload_id
        upload_id = str(uuid4())
        logger.debug(f"Generated upload_id: {upload_id}")

        # Read file content and calculate size
        file_content = await file.read()
        file_size = len(file_content)  # Calculate file size in bytes
        logger.debug(f"File size: {file_size} bytes")

        # Save to a temporary file for uploading
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        temp_file_path = os.path.join(settings.UPLOAD_DIR, f"{upload_id}_{cleaned_filename}")
        logger.debug(f"Saving file locally at: {temp_file_path}")

        async with aiofiles.open(temp_file_path, "wb") as out_file:
            await out_file.write(file_content)

        logger.debug(f"File saved locally. Uploading to Firebase Storage...")

        # Upload file to Firebase Storage
        await asyncio.to_thread(blob.upload_from_filename, temp_file_path, content_type=file.content_type)
        logger.debug(f"File uploaded to Firebase Storage successfully.")

        # Remove the temporary file
        os.remove(temp_file_path)
        logger.debug(f"Temporary file {temp_file_path} removed.")

        # Generate a signed URL
        download_url = blob.generate_signed_url(expiration=timedelta(days=1))
        logger.debug(f"Generated signed URL: {download_url}")

        # Get Firestore client
        firestore_client = get_firestore_client()
        if not firestore_client:
            logger.error("Firestore client is not initialized.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error.",
            )

        # Create Firestore document
        firestore_collection = firestore_client.collection("documents")
        firestore_doc = firestore_collection.document(upload_id)  # Using upload_id as document ID

        document_metadata = {
            "description": description,
            "file_name": cleaned_filename,
            "file_type": file.content_type,
            "file_url": download_url,
            "size": file_size,
            "upload_id": upload_id,
            "uploaded_at": datetime.utcnow(),
            "user_id": admin_user.get("uid"),
        }

        await asyncio.to_thread(firestore_doc.set, document_metadata)
        logger.debug(f"Firestore document {upload_id} created successfully.")

        # Ingest and index the document
        logger.debug("Starting ingestion and indexing of document...")
        await ingest_and_index(download_url, upload_id)

        logger.info(f"File {cleaned_filename} ingested and indexed successfully.")
        return {"message": "Document uploaded and index built successfully.", "download_url": download_url}

    except HTTPException as http_exc:
        logger.exception(f"HTTPException during upload: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception(f"Error uploading and building index: {e}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}"
        )