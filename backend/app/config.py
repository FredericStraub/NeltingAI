# backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import logging

# Configure a logger for the settings
logger = logging.getLogger("settings")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class Settings(BaseSettings):
    ALLOW_ORIGINS: str  # Replace with your frontend's URL
    OPENAI_API_KEY: str
    MODEL: str 
    EMBEDDING_MODEL: str 
    EMBEDDING_DIMENSIONS: int 
    DOCS_DIR: str 
    EXPORT_DIR: str 
    VECTOR_SEARCH_TOP_K: int
    FIREBASE_STORAGE_BUCKET: str 
    SERVICE_ACCOUNT_KEY_PATH: str 
    WEAVIATE_HOST: str 
    WEAVIATE_PORT: int 
    WEAVIATE_GRPC_PORT: int
    WEAVIATE_GRPC_SECURE: bool
    WEAVIATE_HTTP_SECURE: bool
    WEAVIATE_API_KEY: str
    WEAVIATE_URL: str
    MAIN_SYSTEM_PROMPT: str 
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_HOST: str 
    FIREBASE_TYPE: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_PRIVATE_KEY_ID: str
    FIREBASE_PRIVATE_KEY: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_CLIENT_ID: str
    FIREBASE_AUTH_URI: str
    FIREBASE_TOKEN_URI: str
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str
    FIREBASE_CLIENT_X509_CERT_URL: str
    FIREBASE_UNIVERSE_DOMAIN: str
    
    UPLOAD_DIR: str 
    # Frontend Firebase Config fields
    FRONTEND_FIREBASE_API_KEY: str
    FRONTEND_FIREBASE_AUTH_DOMAIN: str
    FRONTEND_FIREBASE_PROJECT_ID: str
    FRONTEND_FIREBASE_STORAGE_BUCKET: str
    FRONTEND_FIREBASE_MESSAGING_SENDER_ID: str
    FRONTEND_FIREBASE_APP_ID: str
    FRONTEND_FIREBASE_MEASUREMENT_ID: str

    # Define Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
    )

    @classmethod
    def customize_sources(cls, init_settings, env_settings, file_secret_settings):
        """
        Customize the order of settings sources to prioritize the `.env` file over environment variables.
        """
        return (
            file_secret_settings,  # Load from .env file first        # Then from environment variables
            init_settings       # Then from initialization parameters
        )


settings = Settings()