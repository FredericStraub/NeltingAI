# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ALLOW_ORIGINS: str = 'http://localhost:5500'  # Replace with your frontend's URL
    OPENAI_API_KEY: str
    LANGCHAIN_MODEL_NAME: str = 'gpt-3.5-turbo'
    EMBEDDING_MODEL: str = 'text-embedding-ada-002'
    EMBEDDING_DIMENSIONS: int = 1024
    DOCS_DIR: str = 'data/docs'
    EXPORT_DIR: str = 'data'
    VECTOR_SEARCH_TOP_K: int = 10
    FIREBASE_STORAGE_BUCKET: str = 'neltingairag-27e31.firebasestorage.app'  
    SERVICE_ACCOUNT_KEY_PATH: str = './serviceAccountKey.json'
    WEAVIATE_HOST: str = 'localhost'
    WEAVIATE_PORT: int = 8080
    MAIN_SYSTEM_PROMPT: str = "Your main system prompt here"
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
    
    # Frontend Firebase Config fields
    FRONTEND_FIREBASE_API_KEY: str
    FRONTEND_FIREBASE_AUTH_DOMAIN: str
    FRONTEND_FIREBASE_PROJECT_ID: str
    FRONTEND_FIREBASE_STORAGE_BUCKET: str
    FRONTEND_FIREBASE_MESSAGING_SENDER_ID: str
    FRONTEND_FIREBASE_APP_ID: str
    FRONTEND_FIREBASE_MEASUREMENT_ID: str

    
    class Config:
        env_file = '/Volumes/External/Netling AI/backend/.env'

    @classmethod
    def model_customise_sources(cls, init_settings, env_settings, file_secret_settings):
        return (
            init_settings,
            file_secret_settings,  # Load .env after env_settings
            env_settings,
        )


settings = Settings()