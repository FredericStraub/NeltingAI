# backend/app/models.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

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

class DocumentOut(BaseModel):
    id: str
    description: Optional[str] = None
    file_name: str
    file_type: str
    file_url: str
    size: int
    upload_id: str
    uploaded_at: datetime
    user_id: str
    
    class Config:
        orm_mode = True
