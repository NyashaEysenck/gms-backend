from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.grant_call import GrantCall
from ..schemas.grant_call import GrantCallCreate, GrantCallUpdate
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

async def create_grant_call(db: AsyncIOMotorDatabase, grant_call_data: GrantCallCreate) -> GrantCall:
    grant_call_dict = grant_call_data.dict()
    grant_call_dict["created_at"] = datetime.utcnow()
    grant_call_dict["updated_at"] = datetime.utcnow()
    result = await db.grant_calls.insert_one(grant_call_dict)
    grant_call_dict["_id"] = result.inserted_id
    return GrantCall(**grant_call_dict)

async def get_grant_call_by_id(db: AsyncIOMotorDatabase, grant_call_id: str) -> Optional[GrantCall]:
    # Try to find by frontend string ID first
    grant_call = await db.grant_calls.find_one({"id": grant_call_id})
    
    # If not found and it's a valid ObjectId, try MongoDB _id
    if not grant_call and ObjectId.is_valid(grant_call_id):
        grant_call = await db.grant_calls.find_one({"_id": ObjectId(grant_call_id)})
    
    if grant_call:
        try:
            return GrantCall(**grant_call)
        except Exception as e:
            print(f"Error creating GrantCall model from data: {e}")
            print(f"Data: {grant_call}")
            return None
    return None

async def get_all_grant_calls(db: AsyncIOMotorDatabase) -> List[GrantCall]:
    grant_calls = []
    try:
        async for grant_call_doc in db.grant_calls.find():
            try:
                grant_call = GrantCall(**grant_call_doc)
                grant_calls.append(grant_call)
            except Exception as e:
                print(f"Error creating GrantCall model from document: {e}")
                print(f"Document: {grant_call_doc}")
                continue
    except Exception as e:
        print(f"Error fetching grant calls from database: {e}")
    
    return grant_calls

async def get_grant_calls_by_type(db: AsyncIOMotorDatabase, grant_type: str) -> List[GrantCall]:
    grant_calls = []
    try:
        async for grant_call_doc in db.grant_calls.find({"type": {"$regex": grant_type, "$options": "i"}}):
            try:
                grant_call = GrantCall(**grant_call_doc)
                grant_calls.append(grant_call)
            except Exception as e:
                print(f"Error creating GrantCall model from document: {e}")
                continue
    except Exception as e:
        print(f"Error fetching grant calls by type: {e}")
    
    return grant_calls

async def get_open_grant_calls(db: AsyncIOMotorDatabase) -> List[GrantCall]:
    grant_calls = []
    try:
        async for grant_call_doc in db.grant_calls.find({"status": "Open"}):
            try:
                grant_call = GrantCall(**grant_call_doc)
                grant_calls.append(grant_call)
            except Exception as e:
                print(f"Error creating GrantCall model from document: {e}")
                continue
    except Exception as e:
        print(f"Error fetching open grant calls: {e}")
    
    return grant_calls

async def update_grant_call(db: AsyncIOMotorDatabase, grant_call_id: str, grant_call_update: GrantCallUpdate) -> Optional[GrantCall]:
    # Try to find by frontend string ID first
    query = {"id": grant_call_id}
    
    # If it's a valid ObjectId, try MongoDB _id instead
    if ObjectId.is_valid(grant_call_id):
        query = {"_id": ObjectId(grant_call_id)}
    
    update_data = {k: v for k, v in grant_call_update.dict().items() if v is not None}
    if not update_data:
        return None
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.grant_calls.update_one(query, {"$set": update_data})
    
    if result.modified_count:
        return await get_grant_call_by_id(db, grant_call_id)
    return None

async def toggle_grant_call_status(db: AsyncIOMotorDatabase, grant_call_id: str) -> Optional[GrantCall]:
    grant_call = await get_grant_call_by_id(db, grant_call_id)
    if not grant_call:
        return None
    
    new_status = "Closed" if grant_call.status == "Open" else "Open"
    
    # Use the same ID format for update as we found the record with
    query = {"id": grant_call_id}
    if ObjectId.is_valid(grant_call_id):
        query = {"_id": ObjectId(grant_call_id)}
    
    result = await db.grant_calls.update_one(
        query,
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        return await get_grant_call_by_id(db, grant_call_id)
    return None

async def delete_grant_call(db: AsyncIOMotorDatabase, grant_call_id: str) -> bool:
    # Try to find by frontend string ID first
    query = {"id": grant_call_id}
    
    # If it's a valid ObjectId, try MongoDB _id instead
    if ObjectId.is_valid(grant_call_id):
        query = {"_id": ObjectId(grant_call_id)}
    
    result = await db.grant_calls.delete_one(query)
    return result.deleted_count > 0