from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Optional
from ..database import get_database
from ..services.document_service import (
    create_document, get_all_documents, get_document_by_id,
    get_documents_by_folder, get_documents_by_user, search_documents,
    upload_new_version, delete_document, delete_document_version, get_document_stats
)
from ..utils.dependencies import get_current_active_user

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    name: str,
    folder: str,
    file: UploadFile = File(...),
    notes: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    if folder not in ["Applications", "Projects", "Awards", "Reports"]:
        raise HTTPException(status_code=400, detail="Invalid folder")
    
    # In real implementation, save file to storage and get actual file size
    file_size = "1MB"  # Placeholder
    
    document = await create_document(
        db, name, folder, file.filename, current_user.email, file_size, notes
    )
    
    return {"id": str(document.id), "message": "Document uploaded successfully"}

@router.get("/")
async def list_documents(
    folder: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    if search:
        is_restricted = current_user.role == "Researcher"
        documents = await search_documents(db, search, current_user.email, is_restricted)
    elif folder:
        documents = await get_documents_by_folder(db, folder)
    elif current_user.role == "Researcher":
        documents = await get_documents_by_user(db, current_user.email)
    else:
        documents = await get_all_documents(db)
    
    return [
        {
            "id": str(doc.id),
            "name": doc.name,
            "folder": doc.folder,
            "current_version": doc.current_version,
            "created_by": doc.created_by,
            "created_at": doc.created_at.isoformat(),
            "last_modified": doc.last_modified.isoformat(),
            "tags": doc.tags
        }
        for doc in documents
    ]

@router.get("/stats")
async def get_stats(current_user = Depends(get_current_active_user)):
    db = await get_database()
    stats = await get_document_stats(db)
    return stats