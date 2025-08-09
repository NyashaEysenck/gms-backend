from pydantic import BaseModel, Field
from typing import Optional

class GrantCallCreate(BaseModel):
    title: str
    type: str
    sponsor: str
    deadline: str
    scope: str
    eligibility: str
    requirements: str
    status: str = "Open"
    visibility: str = "Public"
    
    class Config:
        allow_population_by_field_name = True

class GrantCallUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    sponsor: Optional[str] = None
    deadline: Optional[str] = None
    scope: Optional[str] = None
    eligibility: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

class GrantCallResponse(BaseModel):
    id: str
    title: str
    type: str
    sponsor: str
    deadline: str
    scope: str
    eligibility: str
    requirements: str
    status: str
    visibility: str
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    
    class Config:
        allow_population_by_field_name = True