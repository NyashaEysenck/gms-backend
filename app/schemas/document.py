from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class DocumentVersionCreate(BaseModel):
    filename: str
    file_size: str = Field(alias="fileSize")
    notes: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

class DocumentCreate(BaseModel):
    name: str
    folder: str
    
    class Config:
        allow_population_by_field_name = True

class DocumentVersionResponse(BaseModel):
    id: str
    version_number: int = Field(alias="versionNumber")
    filename: str
    uploaded_by: EmailStr = Field(alias="uploadedBy")
    uploaded_at: str = Field(alias="uploadedAt")
    file_size: str = Field(alias="fileSize")
    notes: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

class DocumentResponse(BaseModel):
    id: str
    name: str
    folder: str
    current_version: int = Field(alias="currentVersion")
    versions: List[DocumentVersionResponse]
    created_by: EmailStr = Field(alias="createdBy")
    created_at: str = Field(alias="createdAt")
    last_modified: str = Field(alias="lastModified")
    tags: List[str] = []
    
    class Config:
        allow_population_by_field_name = True

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    
    class Config:
        allow_population_by_field_name = True