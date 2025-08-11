from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..database import get_database
from ..schemas.user import UserCreate, UserUpdate, UserResponse
from ..services.user_service import (
    create_user, get_all_users, get_user_by_id, 
    update_user, delete_user, reset_user_password
)
from ..utils.dependencies import get_current_active_user, require_role

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_new_user(
    user_data: UserCreate,
    current_user = Depends(require_role("Admin"))
):
    db = await get_database()
    user = await create_user(db, user_data)
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at.isoformat()
    )

@router.get("/", response_model=List[UserResponse])
async def list_users(current_user = Depends(get_current_active_user)):
    db = await get_database()
    users = await get_all_users(db)
    return [
        UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            status=user.status,
            created_at=user.created_at.isoformat()
        )
        for user in users
    ]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user = Depends(require_role("Admin"))
):
    db = await get_database()
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at.isoformat()
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: str,
    user_update: UserUpdate,
    current_user = Depends(require_role("Admin"))
):
    db = await get_database()
    user = await update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at.isoformat()
    )

@router.delete("/{user_id}")
async def delete_user_account(
    user_id: str,
    current_user = Depends(require_role("Admin"))
):
    db = await get_database()
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    current_user = Depends(require_role("Admin"))
):
    db = await get_database()
    temp_password = await reset_user_password(db, user_id)
    if not temp_password:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset successfully", "temporary_password": temp_password}