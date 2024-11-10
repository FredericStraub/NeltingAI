# backend/app/assistants/loader.py
import os
import asyncio
from uuid import uuid4
from tqdm.asyncio import tqdm
from pdfminer.high_level import extract_text
from docx import Document as DocxDocument
from langchain.text_splitter import CharacterTextSplitter
from app.openai import async_get_embedding
from app.config import settings
from app.db import get_weaviate_client

import logging

logger = logging.getLogger(__name__)

async def download_file(url: str) -> bytes:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            else:
                raise RuntimeError(f"Failed to download file from {url}")

async def ingest_and_index(file_url: str):
    try:
        # Download the file content
        file_content = await download_file(file_url)

        # Determine file type
        if file_url.endswith('.pdf'):
            # Save to a temporary file to use pdfminer
            temp_path = 'temp.pdf'
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            text = extract_text(temp_path)
            os.remove(temp_path)
        elif file_url.endswith('.docx'):
            from io import BytesIO
            doc = DocxDocument(BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")

        if not text:
            raise RuntimeError("No text extracted from the document.")

        # Split text into chunks
        text_splitter = CharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=20
        )
        chunks = text_splitter.split_text(text)

        # Embed chunks
        embeddings = []
        logger.info("Embedding document chunks...")
        for chunk in tqdm(chunks, desc="Embedding Chunks"):
            embedding = await async_get_embedding(chunk)
            embeddings.append(embedding)

        # Index into Weaviate
        client = get_weaviate_client()
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            doc_id = f"{uuid4().hex[:8]}-{i}"
            client.data_object.create(
                data_object={
                    "content": chunk,
                    "doc_name": os.path.basename(file_url),
                    "chunk_id": doc_id
                },
                class_name="ChatDocument",
                uuid=doc_id,
                vector=vector
            )
        logger.info(f"Document {file_url} ingested and indexed successfully.")

    except Exception as e:
        logger.error(f"Failed to ingest and index the document: {e}")
        raise e

async def load_knowledge_base():
    # Optional: Implement loading multiple documents
    pass