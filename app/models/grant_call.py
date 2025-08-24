from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from datetime import datetime
from enum import Enum
from bson import ObjectId
from .user import PyObjectId

class GrantType(str, Enum):
    ORI = "ORI"
    EXTERNAL = "External"
    SCHOLARSHIP = "Scholarship"
    TRAVEL_CONFERENCE = "Travel/Conference"
    GOVT = "GOVT"
    FELLOWSHIP = "Fellowship"

class GrantCall(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str
    type: GrantType
    sponsor: str
    deadline: str
    scope: str
    eligibility: str
    requirements: str
    status: str = "Open"  # Open, Closed
    visibility: str = "Public"  # Public, Restricted
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    @validator('created_at', pre=True, always=True)
    def set_created_at(cls, v):
        return v or datetime.utcnow()

    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        return v or datetime.utcnow()

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}