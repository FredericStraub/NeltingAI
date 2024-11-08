import os
import datetime
import logging
import bcrypt
import jwt
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from langfuse import Langfuse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from contextlib import asynccontextmanager

# Updated Imports for LangChain and Weaviate
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth

import nest_asyncio
import aiofiles
from tqdm import tqdm

# Apply nest_asyncio to allow nested event loops (useful for Jupyter notebooks)
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file
load_dotenv(override=True)

# Configuration and Settings
DATABASE_URL = os.getenv("DATABASE_URL")
INDEX_DIR = os.getenv("INDEX_DIR", "./indexes")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
LANGCHAIN_MODEL_NAME = os.getenv("LANGCHAIN_MODEL_NAME", "gpt-3.5-turbo")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")  # Replace with your actual secret key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Ensure this is set in your environment

# Validate essential environment variables
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set in the environment variables.")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

# Initialize database (if needed)
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    engine = None
    Base = declarative_base()

# Directory Configuration
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Database Models (if needed)
class User(Base):
    __tablename__ = "chatusers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )

class UserIn(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    username: str

def get_db():
    if not engine:
        raise RuntimeError("Database engine is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize OpenAI LLM
llm = ChatOpenAI(
    model_name=LANGCHAIN_MODEL_NAME,
    temperature=0.0,
    openai_api_key=OPENAI_API_KEY,
)

# Initialize Weaviate client using WeaviateClient class (v4 API)
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
        "X-OpenAI-Api-Key": OPENAI_API_KEY  # Ensure this is set correctly
    },
    additional_config=AdditionalConfig(
        timeout=Timeout(init=30, query=60, insert=120)  # Adjust as needed
    )
)

# Connect the client (important for v4)
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
            ],
            # Enable multi-tenancy if needed
            # multi_tenancy_config=weaviate.classes.init.Configure.multi_tenancy(enabled=True),
            # Configure indexes if needed
            # vector_index_config=weaviate.classes.init.Configure.VectorIndex.hnsw(
            #     distance_metric=weaviate.classes.init.Configure.VectorDistances.COSINE,
            #     quantizer=weaviate.classes.init.Configure.VectorIndex.Quantizer.bq(),
            # ),
            # inverted_index_config=weaviate.classes.init.Configure.inverted_index(
            #     index_null_state=True,
            #     index_property_length=True,
            #     index_timestamps=True,
            # ),
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

# Function Definitions
def ingest_and_index(file_path: str):
    try:
        # Use appropriate loader based on file extension
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")

        # Load the document
        documents = loader.load()

        if not documents:
            raise RuntimeError("No documents were parsed from the file.")

        # Split documents into chunks
        text_splitter = CharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=20
        )
        docs = text_splitter.split_documents(documents)

        # Initialize embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        # Initialize Weaviate vector store
        vectorstore = WeaviateVectorStore.from_documents(
            docs,
            embeddings,
            client=weaviate_client,
            index_name="ChatDocument",
            text_key="content",
        )

        logger.info("Index successfully updated in Weaviate.")

    except Exception as e:
        logger.error(f"Failed to ingest and index the document: {e}")
        raise RuntimeError(f"Failed to ingest and index the document: {e}")

def build_query_engine():
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        vectorstore = WeaviateVectorStore(
            client=weaviate_client,
            index_name="ChatDocument",
            text_key="content",
            embedding=embeddings,
        )

        # Create a retriever
        retriever = vectorstore.as_retriever()

        # Create the QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever
        )

        logger.info("Query engine successfully built.")
        return qa_chain

    except Exception as e:
        logger.error(f"Failed to build query engine: {e}")
        raise RuntimeError(f"Failed to build query engine: {e}")

# FastAPI Application Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    if DATABASE_URL:
        Base.metadata.create_all(bind=engine)
    yield
    # Close the Weaviate client when the app shuts down
    weaviate_client.close()

app = FastAPI(lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Authentication Functions
def authenticate_user(username: str, password: str, db: Session) -> User | bool:
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.verify_password(password):
        return False
    return user

def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Langfuse Integration
def get_langfuse() -> Langfuse:
    return Langfuse()

def get_trace_handler(
    langfuse: Langfuse = Depends(get_langfuse), user: User = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )
    trace = langfuse.trace(user_id=user.username)
    return trace.get_langchain_handler()

# User Registration and Authentication Endpoints
@app.post("/register", response_model=UserOut)
def register(user_in: UserIn, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = bcrypt.hashpw(user_in.password.encode("utf-8"), bcrypt.gensalt())
    new_user = User(
        username=user_in.username, hashed_password=hashed_password.decode("utf-8")
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refresh to get the new user's data
    return UserOut(username=new_user.username)

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=30)  # Adjust token expiry as needed
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Chat Endpoint
@app.post("/chat/")
async def quick_response(
    question: str,
    user: User = Depends(get_current_user),
    handler: Langfuse = Depends(get_trace_handler),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )

    try:
        query_engine = build_query_engine()

        response = query_engine.run(question)

        return {"response": str(response)}

    except Exception as e:
        logger.error(f"Error processing the query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing the query: {str(e)}")

# Upload Functionality with LangChain
@app.post("/upload-file/")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    handler: Langfuse = Depends(get_trace_handler),
):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".docx")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX are supported.",
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        # Save the uploaded file to disk
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)

        # Ingest and index the document
        ingest_and_index(file_path)

        logger.info(f"File uploaded and indexed: {file.filename}")

        return {"message": "Document uploaded and index built successfully."}

    except Exception as e:
        logger.error(f"Error uploading and building index: {e}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}"
        )

    finally:
        # Clean up the uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)

# Additional Functionalities
@app.post("/build-index/")
def build_index_endpoint(
    file_path: str,
):
    """
    Endpoint to parse a PDF or DOCX file and build indices using LangChain.
    """
    try:
        # Validate if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        # Ingest and index the document
        ingest_and_index(file_path)

        # Build the query engine
        query_engine = build_query_engine()

        # Example Query
        query = "What is the change of free cash flow and what is the rate from the financial and operational highlights?"

        response = query_engine.run(query)
        logger.info("\n************ Query Response ************")
        logger.info(response)

        return {
            "query_response": str(response)
        }

    except FileNotFoundError as fnf_error:
        logger.error(fnf_error)
        raise HTTPException(status_code=400, detail=str(fnf_error))
    except Exception as e:
        logger.error(f"Error building index: {e}")
        raise HTTPException(status_code=500, detail=f"Error building index: {str(e)}")
