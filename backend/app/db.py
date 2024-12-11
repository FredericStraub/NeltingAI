# backend/app/db.py

import weaviate
from app.config import settings
import logging
import time
from fastapi import FastAPI
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.connect import ConnectionParams

logger = logging.getLogger(__name__)


# Function to initialize Weaviate client
def initialize_weaviate_client(app: FastAPI):
    """
    Initialize the Weaviate client and store it in the FastAPI application's state.
    """
    try:
        # Use the connection helper function for local setup
        client = weaviate.WeaviateClient(
            connection_params=ConnectionParams.from_params(
                http_port=settings.WEAVIATE_PORT,
                http_host=settings.WEAVIATE_HOST,
                grpc_port=settings.WEAVIATE_GRPC_PORT,
                http_secure=settings.WEAVIATE_HTTP_SECURE,
                grpc_secure=settings.WEAVIATE_GRPC_SECURE,  
                grpc_host=settings.WEAVIATE_HOST  # Set to True if using gRPC over TLS
            ),
            # Uncomment and replace with your actual API key if needed
            # auth_client_secret=Auth.api_key("your_api_key"),  
            additional_headers={
                "X-OpenAI-Api-Key": settings.OPENAI_API_KEY  # Ensure this is set correctly
            },
            additional_config=AdditionalConfig(
                timeout=Timeout(init=30, query=60, insert=120)  # Adjust as needed
            )
)
        client.connect()
        # Store the client in the application's state
        app.state.weaviate_client = client
        logger.info("Weaviate client initialized and stored in app.state.")
        
    except Exception as e:
        logger.exception(f"Failed to initialize Weaviate client: {e}")
        raise e

# Function to ensure Weaviate schema exists using Collections API (v4)
def ensure_weaviate_schema(app: FastAPI):
    class_name = "ChatDocument"
    try:
        weaviate_client = get_weaviate_client(app)
        # Attempt to retrieve the existing collection
        weaviate_client.collections.get(class_name)
        logger.info(f"Weaviate schema '{class_name}' already exists.")
    except weaviate.exceptions.CollectionNotFoundError:
        # Define the collection schema
        weaviate_client.collections.create(
            name=class_name,
            vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_openai(),
            generative_config=weaviate.classes.config.Configure.Generative.cohere(),
            properties=[
                weaviate.classes.config.Configure.Property(
                    name="content",
                    data_type=weaviate.classes.config.Configure.DataType.TEXT,
                    vectorize_property_name=False,
                    tokenization=weaviate.classes.config.Configure.Tokenization.LOWERCASE,
                ),
                weaviate.classes.config.Configure.Property(
                    name="upload_id",
                    data_type=weaviate.classes.config.Configure.DataType.TEXT,
                    vectorize_property_name=False,
                    tokenization=weaviate.classes.config.Configure.Tokenization.LOWERCASE,
                ),
            ],
        )
        logger.info(f"Weaviate schema '{class_name}' created.")

# Function to test Weaviate connection with retries
def test_weaviate_connection(app: FastAPI, retries: int = 5, delay: int = 5):
    """
    Test the connection to Weaviate with retries.
    """
    weaviate_client = get_weaviate_client(app)
    
    for attempt in range(1, retries + 1):
        try:
            if weaviate_client.is_ready():
                logger.info("Successfully connected to Weaviate.")
                return
            else:
                logger.warning(f"Weaviate is not ready yet (Attempt {attempt}/{retries}). Retrying in {delay} seconds...")
        except Exception as e:
            logger.error(f"Attempt {attempt}/{retries}: Failed to connect to Weaviate: {e}")
        
        time.sleep(delay)
    
    logger.critical("Weaviate is not ready after multiple retries.")
    raise RuntimeError("Weaviate is not ready after multiple retries.")

# Function to retrieve Weaviate client from app state
def get_weaviate_client(app: FastAPI) -> weaviate.Client:
    """
    Retrieve the Weaviate client from the FastAPI application's state.
    """
    client = getattr(app.state, "weaviate_client", None)
    if client is None:
        logger.error("Weaviate client is not initialized.")
        raise RuntimeError("Weaviate client is not initialized.")
    return client

# Function to close Weaviate client
def close_weaviate_client(app: FastAPI):
    """
    Close the Weaviate client connection.
    """
    try:
        weaviate_client = get_weaviate_client(app)
        weaviate_client.close()  # Explicitly close the client
        logger.info("Weaviate client closed successfully.")
    except weaviate.exceptions.WeaviateClosedClientError:
        logger.warning("Weaviate client was already closed.")
    except Exception as e:
        logger.error(f"Error closing Weaviate client: {e}")
