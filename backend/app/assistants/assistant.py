import asyncio
import logging
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings
from app.assistants.tools import QueryKnowledgeBaseTool
from app.utils.sse_stream import SSEStream
from app.db import get_weaviate_client
from app.assistants.prompts import MAIN_SYSTEM_PROMPT
import firebase_admin.firestore as admin_firestore
from datetime import datetime, timezone
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from uuid import uuid4

logger = logging.getLogger(__name__)

# Initialize Langfuse without attaching callbacks
langfuse = Langfuse(
    secret_key=settings.LANGFUSE_SECRET_KEY,
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    host=settings.LANGFUSE_HOST
)

def get_handler():
    """Retrieve the current Langfuse handler from the context."""
    return langfuse_context.get_current_langchain_handler()

def build_chain():
    """Builds the LangChain LLMChain without attaching callbacks."""
    template = """
    Du bist ein Gesundheitsberater und beantwortest ausschließlich Fragen basierend auf den folgenden Textstücken der Familie Nelting. Verwende nur die bereitgestellten Informationen, um hilfreiche und präzise Antworten zu geben. Wenn du die Frage nicht beantworten kannst, empfehle, professionelle Hilfe in Anspruch zu nehmen.

    Kontext:
    {context}

    Frage: {question}
    Antwort:
    """
    prompt = ChatPromptTemplate.from_template(template)

    # Initialize the ChatOpenAI model without callbacks
    model = ChatOpenAI(
        model_name=settings.LANGCHAIN_MODEL_NAME,
        temperature=0.2,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    # Create the LLMChain without callbacks
    chain = LLMChain(llm=model, prompt=prompt, verbose=True)
    return chain

class RAGAssistant:
    def __init__(self, chat_id: str, firestore_client, user_id: str, history_size: int = 4, max_tool_calls: int = 3):
        self.chat_id = chat_id
        self.firestore = firestore_client
        self.user_id = user_id
        self.history_size = history_size
        self.max_tool_calls = max_tool_calls
        
        # Build chain without callbacks
        self.chain = build_chain()

        self.sse_stream = SSEStream()
        self.chat_ref = self.firestore.collection('chats').document(chat_id)
        
        self.initialize_chat()

    def initialize_chat(self):
        try:
            chat_data = self.chat_ref.get().to_dict()
            if not chat_data:
                asyncio.create_task(self._async_firestore_set({
                    'user_id': self.user_id,
                    'created_at': datetime.now(timezone.utc),
                    'messages': []
                }))
                logger.info(f"Initialized new chat with chat_id: {self.chat_id}")
            else:
                logger.info(f"Chat {self.chat_id} already exists.")
        except Exception as e:
            logger.error(f"Failed to initialize chat {self.chat_id}: {e}")

    async def run(self, message: str):
        asyncio.create_task(self._handle_conversation_task(message))
        return self.sse_stream

    @observe()
    async def _handle_conversation_task(self, message: str):
        handler = get_handler()  # Get the current Langfuse handler in context
        callbacks = [handler] if handler else []  # Ensure handler is not None

        try:
            # Append user message to Firestore asynchronously
            user_message = {
                'role': 'user',
                'content': message,
                'created_at': datetime.now(timezone.utc)
            }
            await self._async_firestore_update({
                'messages': admin_firestore.ArrayUnion([user_message])
            })
            logger.info(f"User message appended to chat {self.chat_id}: {message}")

            # Retrieve context from knowledge base
            query_tool = QueryKnowledgeBaseTool()
            context = await query_tool.ainvoke(message)
            logger.debug(f"Retrieved context: {context}")

            # Prepare the query with context and question
            query = {
                "context": context,
                "question": message
            }

            # Execute chain with validated callbacks
            response = await self.chain.ainvoke(query, config={"callbacks": callbacks})
            logger.debug(f"AI Response Type: {type(response)}")
            logger.debug(f"AI Response Content: {response}")

            # Append assistant message to Firestore asynchronously
            assistant_message = {
                'role': 'assistant',
                'content': response,
                'created_at': datetime.now(timezone.utc)
            }
            await self._async_firestore_update({
                'messages': admin_firestore.ArrayUnion([assistant_message])
            })
            logger.info(f"Appended assistant response to chat {self.chat_id}: {response}")

            # Stream the response back to the client
            await self.sse_stream.send(response["text"])
            logger.info(f"Streamed response to client for chat_id {self.chat_id}")

        except Exception as e:
            logger.error(f'Error in conversation task for chat_id {self.chat_id}: {str(e)}')
            await self.sse_stream.send(f"Error: {str(e)}")
        finally:
            await self.sse_stream.close()
            logger.info(f"Closed SSE stream for chat_id {self.chat_id}")

    async def _async_firestore_set(self, data: dict):
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self.chat_ref.set, data)
            logger.debug(f"Set data for chat_id {self.chat_id}: {data}")
        except Exception as e:
            logger.error(f"Failed to set data for chat_id {self.chat_id}: {e}")

    async def _async_firestore_update(self, data: dict):
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self.chat_ref.update, data)
            logger.debug(f"Updated data for chat_id {self.chat_id}: {data}")
        except Exception as e:
            logger.error(f"Failed to update data for chat_id {self.chat_id}: {e}")
            raise e

    async def _async_firestore_get(self):
        loop = asyncio.get_event_loop()
        try:
            chat_snapshot = await loop.run_in_executor(None, self.chat_ref.get)
            logger.debug(f"Fetched data for chat_id {self.chat_id}")
            return chat_snapshot
        except Exception as e:
            logger.error(f"Failed to fetch data for chat_id {self.chat_id}: {e}")
            raise e