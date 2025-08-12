from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    status: str = "active"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class AdminUserUpdate(UserUpdate):
    role: Optional[str] = None
    status: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    status: str
    created_at: str = Field(alias="createdAt")
    
    class Config:
        allow_population_by_field_name = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenWithUser(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    token_type: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class BiodataSchema(BaseModel):
    personal_info: Optional[dict] = None
    contact_info: Optional[dict] = None
    professional_background: Optional[dict] = None
    research_interests: Optional[dict] = None