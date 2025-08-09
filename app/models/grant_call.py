from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class GrantCall(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    type: str
    sponsor: str
    deadline: str
    scope: str
    eligibility: str
    requirements: str
    status: str = "Open"  # Open, Closed
    visibility: str = "Public"  # Public, Restricted
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}