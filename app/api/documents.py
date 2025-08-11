from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import shutil
from pathlib import Path
from ..database import get_database
from ..services.document_service import (
    create_document, get_all_documents, get_document_by_id,
    get_documents_by_folder, get_documents_by_user, search_documents,
    upload_new_version, delete_document, delete_document_version, get_document_stats
)
from ..utils.dependencies import get_current_active_user

router = APIRouter(prefix="/documents", tags=["documents"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_document(
    name: str = Form(...),
    folder: str = Form(...),
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    if folder not in ["Applications", "Projects", "Awards", "Reports"]:
        raise HTTPException(status_code=400, detail="Invalid folder")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, DOCX, and TXT files are allowed.")
    
    # Create folder structure
    folder_path = UPLOAD_DIR / folder / current_user.email
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = str(int(os.path.getmtime(__file__) * 1000))
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = folder_path / safe_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get actual file size
        file_size_bytes = os.path.getsize(file_path)
        file_size = f"{file_size_bytes / 1024:.1f} KB" if file_size_bytes < 1024*1024 else f"{file_size_bytes / (1024*1024):.1f} MB"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create document record in database
    document = await create_document(
        db, name, folder, safe_filename, current_user.email, file_size, notes
    )
    
    return {
        "id": str(document.id), 
        "message": "Document uploaded successfully",
        "filename": safe_filename,
        "size": file_size
    }

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

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    document = await get_document_by_id(db, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions - researchers can only access their own documents
    if current_user.role == "Researcher" and document.created_by != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the latest version
    latest_version = max(document.versions, key=lambda v: v.version_number)
    file_path = UPLOAD_DIR / document.folder / document.created_by / latest_version.file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=latest_version.file_name.split('_', 1)[1] if '_' in latest_version.file_name else latest_version.file_name,
        media_type='application/octet-stream'
    )

@router.post("/{document_id}/upload-version")
async def upload_new_version(
    document_id: str,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    document = await get_document_by_id(db, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions - researchers can only upload to their own documents
    if current_user.role == "Researcher" and document.created_by != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, DOCX, and TXT files are allowed.")
    
    # Create folder structure
    folder_path = UPLOAD_DIR / document.folder / document.created_by
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = str(int(os.path.getmtime(__file__) * 1000))
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = folder_path / safe_filename
    
    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get actual file size
        file_size_bytes = os.path.getsize(file_path)
        file_size = f"{file_size_bytes / 1024:.1f} KB" if file_size_bytes < 1024*1024 else f"{file_size_bytes / (1024*1024):.1f} MB"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Upload new version to database
    success = await upload_new_version(
        db, document_id, safe_filename, current_user.email, file_size, notes
    )
    
    if not success:
        # Clean up file if database operation failed
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to create new version")
    
    return {
        "message": "New version uploaded successfully",
        "filename": safe_filename,
        "size": file_size
    }

@router.get("/stats")
async def get_stats(current_user = Depends(get_current_active_user)):
    db = await get_database()
    stats = await get_document_stats(db)
    return stats