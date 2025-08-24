from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from ...utils.dependencies import get_current_active_user, get_database
from ...schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from ...services.application_service import (
    create_application,
    get_application_by_id,
    get_all_applications,
    get_applications_by_user,
    get_applications_by_status,
    get_applications_by_grant_call,
    update_application
)
from .utils import build_application_response

router = APIRouter()

@router.post("/", response_model=ApplicationResponse)
async def submit_application(
    application_data: ApplicationCreate,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    # Ensure the application is submitted by the current user
    if application_data.email != current_user.email:
        raise HTTPException(status_code=403, detail="Can only submit applications for your own email")
    
    application = await create_application(db, application_data)
    return build_application_response(application)

@router.get("/my", response_model=List[ApplicationResponse])
async def get_my_applications(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user = Depends(get_current_active_user)
):
    """Get applications for the current user (researchers only)"""
    db = await get_database()
    
    # Get applications for current user
    applications = await get_applications_by_user(db, current_user.email)
    if status_filter:
        applications = [app for app in applications if app.status == status_filter]
    
    return [build_application_response(application) for application in applications]

@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    grant_call_id: Optional[str] = Query(None, description="Filter by grant call"),
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    # Regular users can only see their own applications
    if current_user.role == "Researcher":
        applications = await get_applications_by_user(db, current_user.email)
        if status_filter:
            applications = [app for app in applications if app.status == status_filter]
    else:
        # Admins and Grants Managers can see all applications
        if grant_call_id:
            applications = await get_applications_by_grant_call(db, grant_call_id)
        elif status_filter:
            applications = await get_applications_by_status(db, status_filter)
        else:
            applications = await get_all_applications(db)
    
    return [build_application_response(application) for application in applications]

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check access permissions
    if current_user.role == "Researcher" and application.email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return build_application_response(application)

@router.put("/{application_id}/status-admin", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    status_data: dict,
    current_user = Depends(get_current_active_user)
):
    """Update application status (for grants managers and admins)"""
    db = await get_database()
    
    # Only grants managers and admins can update application status
    if current_user.role not in ["Grants Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Only grants managers can update application status")
    
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    new_status = status_data.get("status")
    comments = status_data.get("comments", "")
    
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    # Valid status transitions
    valid_statuses = [
        "submitted", "under_review", "manager_approved", "rejected", 
        "withdrawn", "editable", "needs_revision", "awaiting_signoff", 
        "signoff_approved", "contract_pending", "contract_received"
    ]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    
    # Update application status and comments
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }
    
    if comments:
        update_data["reviewComments"] = comments
        update_data["final_decision"] = new_status
    
    # Set editable flag for certain statuses
    if new_status in ["needs_revision", "editable"]:
        update_data["is_editable"] = True
    else:
        update_data["is_editable"] = False
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update application status")
    
    # Get updated application
    updated_application = await get_application_by_id(db, application_id)
    return build_application_response(updated_application)

@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status_general(
    application_id: str,
    status_data: dict,
    current_user = Depends(get_current_active_user)
):
    """Update application status (unified endpoint for researchers and managers)"""
    db = await get_database()
    
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    new_status = status_data.get("status")
    comments = status_data.get("comments", "")
    
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    # Check permissions based on user role
    if current_user.role == "Researcher":
        # Researchers can only update their own applications
        if application.email != current_user.email:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Researchers can only resubmit (change status to 'submitted')
        if new_status != "submitted":
            raise HTTPException(status_code=403, detail="Researchers can only resubmit applications")
        
        # Can only resubmit if application is in editable state
        if application.status not in ["editable", "needs_revision", "rejected", "withdrawn"]:
            raise HTTPException(status_code=400, detail="Application cannot be resubmitted in current status")
    
    elif current_user.role in ["Grants Manager", "Admin"]:
        # Managers and admins can update any application status
        valid_statuses = [
            "submitted", "under_review", "manager_approved", "rejected", 
            "withdrawn", "editable", "needs_revision", "awaiting_signoff", 
            "signoff_approved", "contract_pending", "contract_received"
        ]
        
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Build update data
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }
    
    if comments:
        update_data["reviewComments"] = comments
        if current_user.role in ["Grants Manager", "Admin"]:
            update_data["final_decision"] = new_status
    
    # Set editable flag for certain statuses
    if new_status in ["needs_revision", "editable"]:
        update_data["is_editable"] = True
    else:
        update_data["is_editable"] = False
    
    # Handle resubmission logic for researchers
    if (new_status == "submitted" and 
        current_user.role == "Researcher" and 
        application.status in ["editable", "needs_revision"]):
        update_data["revision_count"] = (application.revision_count or 0) + 1
        if not application.original_submission_date:
            update_data["original_submission_date"] = application.submission_date
        update_data["submission_date"] = datetime.utcnow().isoformat()
    
    # Update the application
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update application status")
    
    # Get updated application
    updated_application = await get_application_by_id(db, application_id)
    return build_application_response(updated_application)

@router.put("/{application_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_application(
    application_id: str,
    current_user = Depends(get_current_active_user)
):
    """Withdraw application (for researchers)"""
    db = await get_database()
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if user owns this application
    if application.email != current_user.email:
        raise HTTPException(status_code=403, detail="Can only withdraw your own applications")
    
    # Check if application can be withdrawn
    if application.status not in ["submitted", "under_review"]:
        raise HTTPException(status_code=400, detail="Can only withdraw submitted or under review applications")
    
    # Check deadline
    if application.deadline and datetime.now() > datetime.fromisoformat(application.deadline.replace('Z', '+00:00')):
        raise HTTPException(status_code=400, detail="Cannot withdraw application after deadline")
    
    # Update status to withdrawn
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {
            "$set": {
                "status": "withdrawn",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to withdraw application")
    
    # Get updated application
    updated_application = await get_application_by_id(db, application_id)
    return build_application_response(updated_application)

@router.put("/{application_id}/resubmit", response_model=ApplicationResponse)
async def resubmit_application(
    application_id: str,
    status_data: dict,
    current_user = Depends(get_current_active_user)
):
    """Resubmit application after revision"""
    db = await get_database()
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check permissions
    if current_user.role == "Researcher":
        # Researchers can only resubmit their own applications
        if application.email != current_user.email:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Researchers can only change status to 'submitted' (resubmit)
        new_status = status_data.get("status")
        if new_status != "submitted":
            raise HTTPException(status_code=403, detail="Researchers can only resubmit applications")
        
        # Can only resubmit if application is editable or needs revision
        if application.status not in ["editable", "needs_revision", "rejected", "withdrawn"]:
            raise HTTPException(status_code=400, detail="Application cannot be resubmitted in current status")
    
    elif current_user.role in ["Grants Manager", "Admin"]:
        # Grants managers and admins can update any application status
        pass
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    new_status = status_data.get("status")
    comments = status_data.get("comments", "")
    
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    # Update application
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }
    
    if comments:
        update_data["reviewComments"] = comments
    
    # Set editable flag
    if new_status in ["needs_revision", "editable"]:
        update_data["is_editable"] = True
    else:
        update_data["is_editable"] = False
    
    # Handle resubmission
    if new_status == "submitted" and application.status in ["editable", "needs_revision"]:
        update_data["revision_count"] = (application.revision_count or 0) + 1
        if not application.original_submission_date:
            update_data["original_submission_date"] = application.submission_date
        update_data["submission_date"] = datetime.utcnow().isoformat()
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update application")
    
    updated_application = await get_application_by_id(db, application_id)
    return build_application_response(updated_application)

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application_info(
    application_id: str,
    application_update: ApplicationUpdate,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check access permissions
    if current_user.role == "Researcher" and application.email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_application = await update_application(db, application_id, application_update)
    if not updated_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return build_application_response(updated_application)
