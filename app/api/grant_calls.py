from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..database import get_database
from ..schemas.grant_call import GrantCallCreate, GrantCallUpdate, GrantCallResponse
from ..services.grant_call_service import (
    create_grant_call, get_all_grant_calls, get_grant_call_by_id,
    get_grant_calls_by_type, get_open_grant_calls, update_grant_call,
    toggle_grant_call_status, delete_grant_call
)
from ..utils.dependencies import get_current_active_user, require_role

router = APIRouter(prefix="/grant-calls", tags=["grant calls"])

@router.post("/", response_model=GrantCallResponse)
async def create_new_grant_call(
    grant_call_data: GrantCallCreate,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    grant_call = await create_grant_call(db, grant_call_data)
    return GrantCallResponse(
        id=str(grant_call.id),
        title=grant_call.title,
        type=grant_call.type,
        sponsor=grant_call.sponsor,
        deadline=grant_call.deadline,
        scope=grant_call.scope,
        eligibility=grant_call.eligibility,
        requirements=grant_call.requirements,
        status=grant_call.status,
        visibility=grant_call.visibility,
        created_at=grant_call.created_at.isoformat(),
        updated_at=grant_call.updated_at.isoformat()
    )

@router.get("/", response_model=List[GrantCallResponse])
async def list_grant_calls(
    type_filter: Optional[str] = Query(None, description="Filter by grant type"),
    status_filter: Optional[str] = Query(None, description="Filter by status (Open/Closed)"),
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    if status_filter == "Open":
        grant_calls = await get_open_grant_calls(db)
    elif type_filter:
        grant_calls = await get_grant_calls_by_type(db, type_filter)
    else:
        grant_calls = await get_all_grant_calls(db)
    
    return [
        GrantCallResponse(
            id=str(grant_call.id),
            title=grant_call.title,
            type=grant_call.type,
            sponsor=grant_call.sponsor,
            deadline=grant_call.deadline,
            scope=grant_call.scope,
            eligibility=grant_call.eligibility,
            requirements=grant_call.requirements,
            status=grant_call.status,
            visibility=grant_call.visibility,
            created_at=grant_call.created_at.isoformat(),
            updated_at=grant_call.updated_at.isoformat()
        )
        for grant_call in grant_calls
    ]

@router.get("/{grant_call_id}", response_model=GrantCallResponse)
async def get_grant_call(
    grant_call_id: str,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    grant_call = await get_grant_call_by_id(db, grant_call_id)
    if not grant_call:
        raise HTTPException(status_code=404, detail="Grant call not found")
    
    return GrantCallResponse(
        id=str(grant_call.id),
        title=grant_call.title,
        type=grant_call.type,
        sponsor=grant_call.sponsor,
        deadline=grant_call.deadline,
        scope=grant_call.scope,
        eligibility=grant_call.eligibility,
        requirements=grant_call.requirements,
        status=grant_call.status,
        visibility=grant_call.visibility,
        created_at=grant_call.created_at.isoformat(),
        updated_at=grant_call.updated_at.isoformat()
    )

@router.put("/{grant_call_id}", response_model=GrantCallResponse)
async def update_grant_call_info(
    grant_call_id: str,
    grant_call_update: GrantCallUpdate,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    grant_call = await update_grant_call(db, grant_call_id, grant_call_update)
    if not grant_call:
        raise HTTPException(status_code=404, detail="Grant call not found")
    
    return GrantCallResponse(
        id=str(grant_call.id),
        title=grant_call.title,
        type=grant_call.type,
        sponsor=grant_call.sponsor,
        deadline=grant_call.deadline,
        scope=grant_call.scope,
        eligibility=grant_call.eligibility,
        requirements=grant_call.requirements,
        status=grant_call.status,
        visibility=grant_call.visibility,
        created_at=grant_call.created_at.isoformat(),
        updated_at=grant_call.updated_at.isoformat()
    )

@router.patch("/{grant_call_id}/toggle-status", response_model=GrantCallResponse)
async def toggle_status(
    grant_call_id: str,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    grant_call = await toggle_grant_call_status(db, grant_call_id)
    if not grant_call:
        raise HTTPException(status_code=404, detail="Grant call not found")
    
    return GrantCallResponse(
        id=str(grant_call.id),
        title=grant_call.title,
        type=grant_call.type,
        sponsor=grant_call.sponsor,
        deadline=grant_call.deadline,
        scope=grant_call.scope,
        eligibility=grant_call.eligibility,
        requirements=grant_call.requirements,
        status=grant_call.status,
        visibility=grant_call.visibility,
        created_at=grant_call.created_at.isoformat(),
        updated_at=grant_call.updated_at.isoformat()
    )

@router.delete("/{grant_call_id}")
async def delete_grant_call_endpoint(
    grant_call_id: str,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    success = await delete_grant_call(db, grant_call_id)
    if not success:
        raise HTTPException(status_code=404, detail="Grant call not found")
    
    return {"message": "Grant call deleted successfully"}