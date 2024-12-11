# backend/app/assistants/assistant.py
import asyncio
import logging
from operator import itemgetter
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.config import settings
from app.utils.sse_stream import SSEStream
from app.db import get_weaviate_client
import firebase_admin.firestore as admin_firestore
from datetime import datetime, timezone
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.schema import StrOutputParser
from langfuse.callback import CallbackHandler
import os
from fastapi import FastAPI, Request, Depends



# Get keys project from the project settings page


# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def build_chain(app: FastAPI):
    """Builds the LangChain pipeline-style LLMChain integrated with vector retrieval."""
    try:
        # Initialize embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        
        client = get_weaviate_client(app)
        vectorstore = WeaviateVectorStore(
            client=client,
            index_name="ChatDocument",
            text_key="content",
            embedding=embeddings,
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": settings.VECTOR_SEARCH_TOP_K})
        
        # Define the prompt template
        template = """
        Du bist ein Gesundheitsberater und beantwortest ausschließlich Fragen basierend auf den folgenden Textstücken der Familie Nelting. Verwende nur die bereitgestellten Informationen, um hilfreiche und präzise Antworten zu geben. Wenn du die Frage nicht beantworten kannst, empfehle, professionelle Hilfe in Anspruch zu nehmen.
        Hier ist der jetzige Konversationsverlauf zwischen dir und dem jetzigen Nutzer: {history}
        Wenn dieser leer ist, begrüße den Nutzer bitte mit seinem Namen: {name}
        Kontext:
        {context}
    
        Frage: {question}
        Antwort:
        """
        prompt = ChatPromptTemplate.from_template(template)
        
        # Initialize the ChatOpenAI model
        model = ChatOpenAI(
            model_name=settings.MODEL,
            temperature=0.2,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=True
        )
        
        # Build the pipeline-style chain
        chain = (
            {
                "context": itemgetter("question") | retriever,
                "question": itemgetter("question"),
                "name": itemgetter("username"),
                "history": itemgetter("history")
            }
            | prompt
            | model
            | StrOutputParser()
        )
        
        logger.info("Pipeline-style chain successfully built.")
        return chain
    except Exception as e:
        logger.error(f"Failed to build chain: {e}")
        raise e

class RAGAssistant():
    assistants = {}  # Class-level dictionary to store assistant instances

    @classmethod
    def get_assistant(cls, chat_id):
        return cls.assistants.get(chat_id)
    def __init__(self, chat_id: str, firestore_client, user_id: str, user_name: str, history_size: int = 4,app: FastAPI = None):
        self.app = app
        self.chat_id = chat_id
        self.firestore = firestore_client
        self.user_id = user_id
        self.history_size = history_size
        self.user_name = user_name
        # Build pipeline-style chain with integrated retriever
        self.chain = build_chain(self.app)

        self.sse_stream = SSEStream()
        self.chat_ref = self.firestore.collection('chats').document(chat_id)
        
        self.initialize_chat()
        RAGAssistant.assistants[chat_id] = self  # Store instance in class-level dict
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


    async def _handle_conversation_task(self, message: str):
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

            history = await self._fetch_and_format_history()

            # Prepare the query with question (context retrieval is handled by the chain's retriever)
            query = {
                "question": message,
                "username": self.user_name,
                "history": history
            }

            # Initialize LangFuse CallbackHandler
            langfuse_handler = CallbackHandler(public_key=settings.LANGFUSE_PUBLIC_KEY,secret_key=settings.LANGFUSE_SECRET_KEY,host="https://cloud.langfuse.com",session_id=self.chat_id,user_id=self.user_id)
            langfuse_handler.auth_check()
            # Initialize an empty string to collect the assistant's response
            assistant_response = ""

            # Execute the chain with the langfuse_handler
            async for chunk in self.chain.astream(
                query,
                config={"callbacks": [langfuse_handler]}
            ):
                logger.info(repr(chunk))
                # Each chunk is an AIMessageChunk or similar object
                # Extract the content and send it via SSE
                if hasattr(chunk, 'content'):
                    token = chunk.content
                    assistant_response += token
                    await self.sse_stream.send(token)
                else:
                    token = str(chunk)
                    assistant_response += token
                    await self.sse_stream.send(token)

            # After chain execution, store the full assistant response
            assistant_message = {
                'role': 'assistant',
                'content': assistant_response,
                'created_at': datetime.now(timezone.utc)
            }
            await self._async_firestore_update({
                'messages': admin_firestore.ArrayUnion([assistant_message])
            })
            logger.info(f"Appended assistant response to chat {self.chat_id}")

        except Exception as e:
            logger.exception(f'Error in conversation task for chat_id {self.chat_id}')
            await self.sse_stream.send(f"Error: {str(e)}")
        finally:
            await self.sse_stream.close()
            RAGAssistant.assistants.pop(self.chat_id, None)
            logger.info(f"Closed SSE stream for chat_id {self.chat_id}")


    async def _fetch_and_format_history(self) -> str:
        """
        Fetches the last `history_size` messages from Firestore and formats them into a string.
        """
        try:
            chat_snapshot = await self._async_firestore_get()
            messages = chat_snapshot.to_dict().get('messages', [])
            # Ensure messages are sorted by 'created_at'
            messages_sorted = sorted(messages, key=lambda x: x['created_at'])
            # Get the last `history_size` messages
            last_messages = messages_sorted[-self.history_size:]
            # Format messages into a string
            history_str = ""
            for msg in last_messages:
                role = msg.get('role', 'unknown').capitalize()
                content = msg.get('content', '')
                history_str += f"{role}: {content}\n"
            return history_str.strip()
        except Exception as e:
            logger.error(f"Failed to fetch and format history for chat {self.chat_id}: {e}")
            return ""    
        
    async def handle_message(self, message: str):
        self.message = message
        self.process_task = asyncio.create_task(self._handle_conversation_task(message))

    async def get_stream(self):
        return self.sse_stream

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