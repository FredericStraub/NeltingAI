# backend/app/models.py
from pydantic import BaseModel

class UserOut(BaseModel):
    uid: str
    email: str

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    message: str

class UserIn(BaseModel):
    email: str
    password: str
    username: str  # Added username field

class UserOut(BaseModel):
    uid: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str