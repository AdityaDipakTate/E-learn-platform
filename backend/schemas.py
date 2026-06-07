from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

# --- LESSON SCHEMAS ---
class LessonBase(BaseModel):
    id: int
    title: str
    content: str
    video_url: Optional[str] = None

    # This tells Pydantic to read data even if it's not a dict, but an ORM model
    model_config = ConfigDict(from_attributes=True)

# --- COURSE SCHEMAS ---
class CourseBase(BaseModel):
    id: int
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True)

    # --- USER SCHEMAS ---
# class UserCreate(BaseModel):
#     username: str
#     email: str
#     password: str = Field(..., max_length=72, description="Password cannot exceed 72 characters")
from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    username: str
    email: str
    password: str = Field(..., description="Password cannot exceed 72 bytes")

    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        # Measure length in UTF-8 bytes instead of string characters
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must not exceed 72 bytes when encoded')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)

# --- AUTH SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- PROGRESS SCHEMAS ---
class ProgressUpdate(BaseModel):
    lesson_id: int
    is_completed: bool = True