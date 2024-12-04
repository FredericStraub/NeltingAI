# backend/app/db.py

import weaviate
from app.config import settings
import logging
import time
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from weaviate.connect import ConnectionParams

logger = logging.getLogger(__name__)

# Initialize Weaviate client using the standard Client class
weaviate_client = weaviate.WeaviateClient(
    connection_params=ConnectionParams.from_params(
        http_host="localhost",       # Replace with your Weaviate HTTP host
        http_port=8080,              # Replace with your Weaviate HTTP port
        http_secure=False,           # Set to True if using HTTPS
        grpc_host="localhost",       # Replace with your Weaviate gRPC host
        grpc_port=50051,             # Replace with your Weaviate gRPC port
        grpc_secure=False,           # Set to True if using gRPC over TLS
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
# Function to ensure Weaviate schema exists
weaviate_client.connect()

# Function to ensure Weaviate schema exists using Collections API (v4)
def ensure_weaviate_schema():
    class_name = "ChatDocument"
    try:
        # Attempt to retrieve the existing collection
        weaviate_client.collections.get(class_name)
        logger.info(f"Weaviate schema '{class_name}' already exists.")
    except weaviate.exceptions.CollectionNotFoundError:
        # Define the collection schema
        collection = weaviate_client.collections.create(
            name=class_name,
            vectorizer_config=weaviate.classes.init.Configure.Vectorizer.text2vec_openai(),  # Use OpenAI for vectorization
            generative_config=weaviate.classes.init.Configure.Generative.cohere(),           # Use Cohere for RAG
            properties=[
                weaviate.classes.init.Configure.Property(
                    name="content",
                    data_type=weaviate.classes.init.Configure.DataType.TEXT,
                    vectorize_property_name=False,  # Do not include property name in vectorization
                    tokenization=weaviate.classes.init.Configure.Tokenization.LOWERCASE,  # Use lowercase tokenization
                ),
                weaviate.classes.init.Configure.Property(
                    name="upload_id",
                    data_type=weaviate.classes.init.Configure.DataType.TEXT,
                    vectorize_property_name=False,  # Do not include property name in vectorization
                    tokenization=weaviate.classes.init.Configure.Tokenization.LOWERCASE,  # Use lowercase tokenization
                ),
            ],
        )
        logger.info(f"Weaviate schema '{class_name}' created.")

# Call the schema creation function
ensure_weaviate_schema()

# Test Weaviate connection with retries
def test_weaviate_connection(retries=5, delay=5):
    for attempt in range(retries):
        try:
            ready = weaviate_client.is_ready()
            if ready:
                logger.info("Successfully connected to Weaviate.")
                return
            else:
                logger.warning(f"Weaviate is not ready yet (Attempt {attempt + 1}/{retries}). Retrying in {delay} seconds...")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{retries}: Failed to connect to Weaviate: {e}")
        time.sleep(delay)
    raise RuntimeError("Weaviate is not ready after multiple retries.")

# Call the connection test function
test_weaviate_connection()

def get_weaviate_client():
    return weaviate_client

# Function to close Weaviate client (if necessary)
def close_weaviate_client():
    try:
        # The standard weaviate.Client does not have a close method.
        # If using a custom client that requires closure, implement it here.
        pass
    except Exception as e:
        logger.error(f"Error closing Weaviate client: {e}")