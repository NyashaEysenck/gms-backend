from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.grant_call import GrantCall
from ..schemas.grant_call import GrantCallCreate, GrantCallUpdate
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

async def create_grant_call(db: AsyncIOMotorDatabase, grant_call_data: GrantCallCreate) -> GrantCall:
    grant_call_dict = grant_call_data.dict()
    result = await db.grant_calls.insert_one(grant_call_dict)
    grant_call_dict["_id"] = result.inserted_id
    return GrantCall(**grant_call_dict)

async def get_grant_call_by_id(db: AsyncIOMotorDatabase, grant_call_id: str) -> Optional[GrantCall]:
    if not ObjectId.is_valid(grant_call_id):
        return None
    grant_call = await db.grant_calls.find_one({"_id": ObjectId(grant_call_id)})
    if grant_call:
        return GrantCall(**grant_call)
    return None

async def get_all_grant_calls(db: AsyncIOMotorDatabase) -> List[GrantCall]:
    grant_calls = []
    async for grant_call in db.grant_calls.find():
        grant_calls.append(GrantCall(**grant_call))
    return grant_calls

async def get_grant_calls_by_type(db: AsyncIOMotorDatabase, grant_type: str) -> List[GrantCall]:
    grant_calls = []
    async for grant_call in db.grant_calls.find({"type": {"$regex": grant_type, "$options": "i"}}):
        grant_calls.append(GrantCall(**grant_call))
    return grant_calls

async def get_open_grant_calls(db: AsyncIOMotorDatabase) -> List[GrantCall]:
    grant_calls = []
    async for grant_call in db.grant_calls.find({"status": "Open"}):
        grant_calls.append(GrantCall(**grant_call))
    return grant_calls

async def update_grant_call(db: AsyncIOMotorDatabase, grant_call_id: str, grant_call_update: GrantCallUpdate) -> Optional[GrantCall]:
    if not ObjectId.is_valid(grant_call_id):
        return None
    
    update_data = {k: v for k, v in grant_call_update.dict().items() if v is not None}
    if not update_data:
        return None
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.grant_calls.update_one(
        {"_id": ObjectId(grant_call_id)}, 
        {"$set": update_data}
    )
    
    if result.modified_count:
        return await get_grant_call_by_id(db, grant_call_id)
    return None

async def toggle_grant_call_status(db: AsyncIOMotorDatabase, grant_call_id: str) -> Optional[GrantCall]:
    if not ObjectId.is_valid(grant_call_id):
        return None
    
    grant_call = await get_grant_call_by_id(db, grant_call_id)
    if not grant_call:
        return None
    
    new_status = "Closed" if grant_call.status == "Open" else "Open"
    
    result = await db.grant_calls.update_one(
        {"_id": ObjectId(grant_call_id)},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        return await get_grant_call_by_id(db, grant_call_id)
    return None

async def delete_grant_call(db: AsyncIOMotorDatabase, grant_call_id: str) -> bool:
    if not ObjectId.is_valid(grant_call_id):
        return False
    result = await db.grant_calls.delete_one({"_id": ObjectId(grant_call_id)})
    return result.deleted_count > 0