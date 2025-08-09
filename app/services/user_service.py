from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.user import User, UserInDB
from ..schemas.user import UserCreate, UserUpdate
from ..utils.security import get_password_hash, verify_password
from typing import Optional, List
from bson import ObjectId

async def create_user(db: AsyncIOMotorDatabase, user_data: UserCreate) -> User:
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return User(**user_dict)

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[UserInDB]:
    user = await db.users.find_one({"email": email})
    if user:
        return UserInDB(**user)
    return None

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[User]:
    if not ObjectId.is_valid(user_id):
        return None
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(**user)
    return None

async def get_all_users(db: AsyncIOMotorDatabase) -> List[User]:
    users = []
    async for user in db.users.find():
        users.append(User(**user))
    return users

async def update_user(db: AsyncIOMotorDatabase, user_id: str, user_update: UserUpdate) -> Optional[User]:
    if not ObjectId.is_valid(user_id):
        return None
    
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    if not update_data:
        return None
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": update_data}
    )
    
    if result.modified_count:
        return await get_user_by_id(db, user_id)
    return None

async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    if not ObjectId.is_valid(user_id):
        return False
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str, role: str = None) -> Optional[UserInDB]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    # Only check role if it's provided (for backward compatibility)
    if role is not None and user.role != role:
        return None
    return user

async def reset_user_password(db: AsyncIOMotorDatabase, user_id: str) -> Optional[str]:
    import secrets
    import string
    
    if not ObjectId.is_valid(user_id):
        return None
    
    # Generate temporary password
    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    hashed_password = get_password_hash(temp_password)
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    if result.modified_count:
        return temp_password
    return None