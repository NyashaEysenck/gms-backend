from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class DocumentVersion(BaseModel):
    id: str
    version_number: int = Field(alias="versionNumber")
    filename: str
    uploaded_by: EmailStr = Field(alias="uploadedBy")
    uploaded_at: datetime = Field(alias="uploadedAt")
    file_size: str = Field(alias="fileSize")
    notes: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

class Document(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    folder: str  # Applications, Projects, Awards, Reports
    current_version: int = Field(alias="currentVersion")
    versions: List[DocumentVersion]
    created_by: EmailStr = Field(alias="createdBy")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    last_modified: datetime = Field(default_factory=datetime.utcnow, alias="lastModified")
    tags: List[str] = []

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}