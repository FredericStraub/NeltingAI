# backend/app/models.py

from pydantic import BaseModel

class User(BaseModel):
    uid: str
    email: str
    username: str
    # Add other relevant fields as needed

class UserIn(BaseModel):
    email: str
    password: str
    username: str  # Added username field

class UserOut(BaseModel):
    uid: str
    email: str
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    message: str

class AdminAssignRole(BaseModel):
    uid: str
    role: str  # Expected to be "admin" or other roles