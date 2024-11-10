# backend/app/api/upload.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import os
import aiofiles
import logging
from datetime import timedelta

from app.api.admin import get_current_admin  # Correct dependency
from app.loader import ingest_and_index
from app.config import settings
from app.firebase import get_storage_bucket

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/upload-file/", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    admin_uid: str = Depends(get_current_admin),  # Correct dependency
):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".docx")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX are supported.",
        )

    # Define the storage path in Firebase Storage
    storage_bucket = get_storage_bucket()
    blob = storage_bucket.blob(f"uploads/{admin_uid}/{file.filename}")

    try:
        # Save the uploaded file to disk
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Upload file to Firebase Storage
        await blob.upload_from_filename(file_path, content_type=file.content_type)
        os.remove(file_path)  # Clean up the local file

        # Generate a signed URL for the uploaded file (valid for 1 day)
        download_url = blob.generate_signed_url(expiration=timedelta(days=1))

        # Ingest and index the document using the download URL
        await ingest_and_index(download_url)

        logger.info(f"File {file.filename} ingested and indexed successfully.")

        return {"message": "Document uploaded and index built successfully.", "download_url": download_url}

    except Exception as e:
        logger.error(f"Error uploading and building index: {e}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}"
        )