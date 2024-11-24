# backend/app/api/upload.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import os
import aiofiles
import logging
from datetime import timedelta
import asyncio
from app.api.dependencies import get_current_admin  # Assuming only admins can upload
from app.loader import ingest_and_index
from app.config import settings
from app.firebase import get_storage_bucket

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/upload-file/", status_code=201, tags=["Upload"])
async def upload_file(
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
        blob = storage_bucket.blob(f"uploads/{admin_user.get('uid')}/{file.filename}")
        logger.debug(f"Firebase blob path: uploads/{admin_user.get('uid')}/{file.filename}")

        # Log file processing steps
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        logger.debug(f"Saving file locally at: {file_path}")
        
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        logger.debug(f"File saved locally. Uploading to Firebase...")

        # Upload file to Firebase Storage
        await asyncio.to_thread(blob.upload_from_filename, file_path, content_type=file.content_type)
        os.remove(file_path)
        logger.debug(f"File uploaded to Firebase successfully. Generating signed URL...")

        # Generate a signed URL
        download_url = blob.generate_signed_url(expiration=timedelta(days=1))
        logger.debug(f"Generated signed URL: {download_url}")

        # Ingest and index the document
        logger.debug("Starting ingestion and indexing of document...")
        await ingest_and_index(download_url)

        logger.info(f"File {file.filename} ingested and indexed successfully.")
        return {"message": "Document uploaded and index built successfully.", "download_url": download_url}

    except Exception as e:
        logger.exception(f"Error uploading and building index: {e}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}"
        )