# test_chain.py

import asyncio
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import logging

# Import Settings from config.py
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def build_chain():
    template = """
    Du bist ein Gesundheitsberater und beantwortest ausschließlich Fragen basierend auf den folgenden Textstücken der Familie Nelting. Verwende nur die bereitgestellten Informationen, um hilfreiche und präzise Antworten zu geben. Wenn du die Frage nicht beantworten kannst, empfehle, professionelle Hilfe in Anspruch zu nehmen.

    Kontext:
    {context}

    Frage: {question}
    Antwort:
    Bitte antworte nur mit dem Text der Antwort, ohne zusätzliche Metadaten oder Struktur.
    """

    prompt = ChatPromptTemplate.from_template(template)

    # Initialize Langfuse CallbackHandler (mocked for testing)
    langfuse_handler = None  # Replace with actual handler if needed

    logger.info("Langfuse CallbackHandler successfully initialized.")

    model = ChatOpenAI(
        model_name=settings.MODEL,
        temperature=0.2,  # Adjusted for more dynamic responses
        openai_api_key=settings.OPENAI_API_KEY,
        callbacks=[]  # Removed Langfuse callbacks for testing
    )

    # Create chain without Langfuse for testing
    chain = LLMChain(llm=model, prompt=prompt, callbacks=[], verbose=True)
    return chain

async def test_chain():
    chain = build_chain()
    query = {
        "context": "Fritjof Nelting, Jahrgang 1983, ist Geschäftsführer der Gezeiten Haus Gruppe mit Sitz in Wesseling bei Köln. Er beschäftigt sich intensiv mit der Verbindung westlicher Psychosomatik und Traditioneller Chinesischer Medizin.",
        "question": "Wer ist Fritjof?"
    }
    response = await chain.ainvoke(query)
    print("AI Response:", response)

if __name__ == "__main__":
    asyncio.run(test_chain())