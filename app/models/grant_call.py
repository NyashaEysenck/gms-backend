from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class GrantCall(BaseModel):
    id: Optional[Union[str, PyObjectId]] = Field(None, alias="_id")
    frontend_id: Optional[str] = Field(None, alias="id")  # Handle frontend string IDs
    title: str
    type: str
    sponsor: str
    deadline: str
    scope: str
    eligibility: str
    requirements: str
    status: str = "Open"  # Open, Closed
    visibility: str = "Public"  # Public, Restricted
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    @validator('id', pre=True, always=True)
    def set_id(cls, v, values):
        # If we have a frontend_id (string), use that as the main id
        if 'frontend_id' in values and values['frontend_id']:
            return values['frontend_id']
        # Otherwise use the MongoDB _id
        return v or PyObjectId()

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