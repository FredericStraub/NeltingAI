# backend/app/assistants/tools.py

from pydantic import BaseModel
from langchain.tools import BaseTool
from langchain_weaviate.vectorstores import WeaviateVectorStore
from app.config import settings
from app.db import get_weaviate_client
from langchain_openai import OpenAIEmbeddings
import logging

logger = logging.getLogger(__name__)

class QueryKnowledgeBaseTool(BaseTool, BaseModel):
    """
    Tool to query the knowledge base to answer user questions about new technology trends,
    their applications, and broader impacts.
    """
    
    name: str = "QueryKnowledgeBaseTool"
    description: str = (
        "Useful for answering questions about new technology trends, their applications, "
        "and broader impacts by querying the knowledge base."
    )

    def _run(self, query_input: str):
        raise NotImplementedError("This tool supports only async operation.")

    async def _arun(self, query_input: str):
        """
        Asynchronous implementation using Weaviate to query the knowledge base.
        """
        try:
            client = get_weaviate_client()
            embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            vectorstore = WeaviateVectorStore(
                client=client,
                index_name="ChatDocument",
                text_key="content",
                embedding=embeddings,  # Correct parameter
            )
            retriever = vectorstore.as_retriever(search_kwargs={"k": settings.VECTOR_SEARCH_TOP_K})
            results = await retriever.ainvoke(query_input)

            formatted_sources = [
                f"SOURCE: {doc.metadata.get('source', 'Unknown')}\n\"\"\"\n{doc.page_content}\n\"\"\""
                for doc in results
            ]
            context = "\n\n---\n\n".join(formatted_sources) + "\n\n---"
            logger.debug(f"Formatted context: {context}")
            return context  # Returns a string
        except Exception as e:
            logger.exception(f"Error querying knowledge base: {e}")  # Logs stack trace
            return f"Error querying knowledge base: {str(e)}"