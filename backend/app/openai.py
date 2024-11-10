# backend/app/openai.py
import asyncio
import openai
from app.config import settings

openai.api_key = settings.OPENAI_API_KEY

def get_chat_model():
    return openai.ChatCompletion

def get_embedding(input_text: str, model: str = settings.EMBEDDING_MODEL) -> list:
    try:
        response = openai.Embedding.create(
            input=[input_text],
            model=model
        )
        return response['data'][0]['embedding']
    except Exception as e:
        raise e

async def async_get_embedding(input_text: str, model: str = settings.EMBEDDING_MODEL) -> list:
    return await asyncio.to_thread(get_embedding, input_text, model)