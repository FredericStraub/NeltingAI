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