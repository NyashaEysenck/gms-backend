from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.document import Document, DocumentVersion
from typing import Optional, List
from bson import ObjectId
from datetime import datetime
import secrets

async def create_document(db: AsyncIOMotorDatabase, name: str, folder: str, filename: str, uploaded_by: str, file_size: str, notes: str = None) -> Document:
    document_id = f"doc_{secrets.token_hex(8)}"
    
    first_version = DocumentVersion(
        id=f"{document_id}_v1",
        version_number=1,
        filename=filename,
        uploaded_by=uploaded_by,
        uploaded_at=datetime.utcnow(),
        file_size=file_size,
        notes=notes
    )
    
    document_data = {
        "name": name,
        "folder": folder,
        "current_version": 1,
        "versions": [first_version.dict()],
        "created_by": uploaded_by,
        "tags": []
    }
    
    result = await db.documents.insert_one(document_data)
    document_data["_id"] = result.inserted_id
    return Document(**document_data)

async def get_document_by_id(db: AsyncIOMotorDatabase, document_id: str) -> Optional[Document]:
    if not ObjectId.is_valid(document_id):
        return None
    document = await db.documents.find_one({"_id": ObjectId(document_id)})
    if document:
        return Document(**document)
    return None

async def get_all_documents(db: AsyncIOMotorDatabase) -> List[Document]:
    documents = []
    async for document in db.documents.find():
        documents.append(Document(**document))
    return documents

async def get_documents_by_folder(db: AsyncIOMotorDatabase, folder: str) -> List[Document]:
    documents = []
    async for document in db.documents.find({"folder": folder}):
        documents.append(Document(**document))
    return documents

async def get_documents_by_user(db: AsyncIOMotorDatabase, user_email: str) -> List[Document]:
    documents = []
    async for document in db.documents.find({"versions.uploaded_by": user_email}):
        documents.append(Document(**document))
    return documents

async def search_documents(db: AsyncIOMotorDatabase, query: str, user_email: str = None, is_restricted_user: bool = False) -> List[Document]:
    search_filter = {}
    
    if is_restricted_user and user_email:
        search_filter["versions.uploaded_by"] = user_email
    
    if query.strip():
        search_filter["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"versions.filename": {"$regex": query, "$options": "i"}},
            {"tags": {"$regex": query, "$options": "i"}}
        ]
    
    documents = []
    async for document in db.documents.find(search_filter):
        documents.append(Document(**document))
    return documents

async def upload_new_version(db: AsyncIOMotorDatabase, document_id: str, filename: str, uploaded_by: str, file_size: str, notes: str = None) -> Optional[Document]:
    if not ObjectId.is_valid(document_id):
        return None
    
    document = await get_document_by_id(db, document_id)
    if not document:
        return None
    
    new_version_number = document.current_version + 1
    new_version = DocumentVersion(
        id=f"{document_id}_v{new_version_number}",
        version_number=new_version_number,
        filename=filename,
        uploaded_by=uploaded_by,
        uploaded_at=datetime.utcnow(),
        file_size=file_size,
        notes=notes
    )
    
    result = await db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {
            "$push": {"versions": new_version.dict()},
            "$set": {
                "current_version": new_version_number,
                "last_modified": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return await get_document_by_id(db, document_id)
    return None

async def delete_document(db: AsyncIOMotorDatabase, document_id: str) -> bool:
    if not ObjectId.is_valid(document_id):
        return False
    result = await db.documents.delete_one({"_id": ObjectId(document_id)})
    return result.deleted_count > 0

async def delete_document_version(db: AsyncIOMotorDatabase, document_id: str, version_id: str) -> Optional[Document]:
    if not ObjectId.is_valid(document_id):
        return None
    
    document = await get_document_by_id(db, document_id)
    if not document or len(document.versions) <= 1:
        return None
    
    result = await db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {
            "$pull": {"versions": {"id": version_id}},
            "$set": {"last_modified": datetime.utcnow()}
        }
    )
    
    if result.modified_count:
        # Update current version if we deleted the current one
        updated_document = await get_document_by_id(db, document_id)
        if updated_document and updated_document.versions:
            max_version = max(v.version_number for v in updated_document.versions)
            await db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"current_version": max_version}}
            )
        return await get_document_by_id(db, document_id)
    return None

async def get_document_stats(db: AsyncIOMotorDatabase) -> dict:
    pipeline = [
        {"$group": {"_id": "$folder", "count": {"$sum": 1}}},
        {"$group": {"_id": None, "folders": {"$push": {"folder": "$_id", "count": "$count"}}, "total": {"$sum": "$count"}}}
    ]
    
    result = await db.documents.aggregate(pipeline).to_list(1)
    
    if result:
        stats = {"total": result[0]["total"]}
        for folder_stat in result[0]["folders"]:
            stats[folder_stat["folder"]] = folder_stat["count"]
        
        # Add missing folders with 0 count
        for folder in ["Applications", "Projects", "Awards", "Reports"]:
            if folder not in stats:
                stats[folder] = 0
                
        return stats
    
    return {"total": 0, "Applications": 0, "Projects": 0, "Awards": 0, "Reports": 0}