# backend/app/api/index.py
from fastapi import APIRouter, HTTPException, Depends
import logging

from app.loader import ingest_and_index
from app.config import settings
from app.api.auth import verify_firebase_token

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/build-index/")
async def build_index_endpoint(
    file_url: str,
    uid: str = Depends(verify_firebase_token),
):
    """
    Endpoint to parse a PDF or DOCX file and build indices using LangChain.
    """
    try:
        # Ingest and index the document from the provided URL
        await ingest_and_index(file_url)

        logger.info(f"Index built for file: {file_url}")

        return {"message": "Index built successfully."}

    except Exception as e:
        logger.error(f"Error building index: {e}")
        raise HTTPException(status_code=500, detail=f"Error building index: {str(e)}")