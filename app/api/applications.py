from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import FileResponse, Response
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import base64
from ..utils.dependencies import get_current_active_user, get_database, require_role
from ..schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from ..services.application_service import create_application, get_application_by_id, get_all_applications, get_applications_by_user, get_applications_by_status, get_applications_by_grant_call, update_application
import os
from pathlib import Path

router = APIRouter(prefix="/applications", tags=["applications"])

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
    return ApplicationResponse(
        id=str(application.id),
        grant_id=application.grant_id,
        applicant_name=application.applicant_name,
        email=application.email,
        proposal_title=application.proposal_title,
        status=application.status,
        submission_date=application.submission_date,
        review_comments=application.review_comments,
        biodata=application.biodata,
        deadline=application.deadline,
        proposal_file_name=application.proposal_file_name,
        proposal_file_size=application.proposal_file_size,
        proposal_file_type=application.proposal_file_type
    )

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
    
    return [
        ApplicationResponse(
            id=str(application.id),
            grant_id=application.grant_id,
            applicant_name=application.applicant_name,
            email=application.email,
            proposal_title=application.proposal_title,
            status=application.status,
            submission_date=application.submission_date,
            review_comments=application.review_comments,
            biodata=application.biodata,
            deadline=application.deadline,
            proposal_file_name=application.proposal_file_name,
            proposal_file_size=application.proposal_file_size,
            proposal_file_type=application.proposal_file_type
        )
        for application in applications
    ]

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
    
    return [
        ApplicationResponse(
            id=str(application.id),
            grant_id=application.grant_id,
            applicant_name=application.applicant_name,
            email=application.email,
            proposal_title=application.proposal_title,
            status=application.status,
            submission_date=application.submission_date,
            review_comments=application.review_comments,
            biodata=application.biodata,
            deadline=application.deadline,
            proposal_file_name=application.proposal_file_name,
            proposal_file_size=application.proposal_file_size,
            proposal_file_type=application.proposal_file_type
        )
        for application in applications
    ]

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
    
    return ApplicationResponse(
        id=str(application.id),
        grant_id=application.grant_id,
        applicant_name=application.applicant_name,
        email=application.email,
        proposal_title=application.proposal_title,
        status=application.status,
        submission_date=application.submission_date,
        review_comments=application.review_comments,
        biodata=application.biodata,
        deadline=application.deadline,
        proposal_file_name=application.proposal_file_name,
        proposal_file_size=application.proposal_file_size,
        proposal_file_type=application.proposal_file_type
    )

@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    status_data: dict,
    current_user = Depends(get_current_active_user)
):
    """Update application status (for grants managers and admins)"""
    db = await get_database()
    
    # Only grants managers and admins can update status
    if current_user.role not in ["Grants Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Only grants managers can update application status")
    
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update application status
    new_status = status_data.get("status")
    comments = status_data.get("comments", "")
    
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    # Update the application
    update_data = {"status": new_status}
    if comments:
        update_data["review_comments"] = comments
    
    # Handle special status updates
    if new_status == "needs_revision":
        update_data["is_editable"] = True
    elif new_status == "editable":
        update_data["is_editable"] = True
    else:
        update_data["is_editable"] = False
    
    # Update in database
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update application")
    
    # Get updated application
    updated_application = await get_application_by_id(db, application_id)
    
    return ApplicationResponse(
        id=str(updated_application.id),
        grant_id=updated_application.grant_id,
        applicant_name=updated_application.applicant_name,
        email=updated_application.email,
        proposal_title=updated_application.proposal_title,
        status=updated_application.status,
        submission_date=updated_application.submission_date,
        review_comments=updated_application.review_comments,
        biodata=updated_application.biodata,
        deadline=updated_application.deadline,
        proposal_file_name=updated_application.proposal_file_name,
        proposal_file_size=updated_application.proposal_file_size,
        proposal_file_type=updated_application.proposal_file_type
    )

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
    
    # Check permissions - only the applicant can withdraw
    if application.email != current_user.email:
        raise HTTPException(status_code=403, detail="You can only withdraw your own applications")
    
    # Check if withdrawal is allowed
    if application.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted applications can be withdrawn")
    
    # Check deadline
    if application.deadline and datetime.utcnow() > datetime.fromisoformat(application.deadline.replace('Z', '+00:00')):
        raise HTTPException(status_code=400, detail="Cannot withdraw application after deadline")
    
    # Update status to withdrawn
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": {"status": "withdrawn"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to withdraw application")
    
    # Get updated application
    updated_application = await get_application_by_id(db, application_id)
    
    return ApplicationResponse(
        id=str(updated_application.id),
        grant_id=updated_application.grant_id,
        applicant_name=updated_application.applicant_name,
        email=updated_application.email,
        proposal_title=updated_application.proposal_title,
        status=updated_application.status,
        submission_date=updated_application.submission_date,
        review_comments=updated_application.review_comments,
        biodata=updated_application.biodata,
        deadline=updated_application.deadline,
        proposal_file_name=updated_application.proposal_file_name,
        proposal_file_size=updated_application.proposal_file_size,
        proposal_file_type=updated_application.proposal_file_type
    )

@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    status_data: dict,
    current_user = Depends(get_current_active_user)
):
    """Update application status"""
    print(f"DEBUG: Status update endpoint called for application {application_id}")
    print(f"DEBUG: Status data: {status_data}")
    print(f"DEBUG: Current user: {current_user.email} (role: {current_user.role})")
    
    db = await get_database()
    
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check permissions based on status change
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    # Researchers can only resubmit their own applications
    if current_user.role == "Researcher":
        print(f"DEBUG: Current user email: '{current_user.email}'")
        print(f"DEBUG: Application email: '{application.email}'")
        print(f"DEBUG: Email match: {application.email == current_user.email}")
        print(f"DEBUG: Current user role: '{current_user.role}'")
        print(f"DEBUG: New status: '{new_status}'")
        
        if application.email != current_user.email:
            raise HTTPException(status_code=403, detail="You can only update your own applications")
        if new_status not in ["submitted", "editable"]:
            raise HTTPException(status_code=403, detail="Researchers can only resubmit or edit applications")
    
    # Grants managers can update any application status
    elif current_user.role not in ["Grants Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="You do not have permission to update application status")
    
    # Update the application status
    update_data = {"status": new_status}
    if status_data.get("comments"):
        update_data["review_comments"] = status_data["comments"]
    
    # If resubmitting, update submission date and make non-editable
    if new_status == "submitted":
        update_data["submission_date"] = datetime.utcnow().isoformat()
        update_data["is_editable"] = False
    elif new_status == "editable":
        update_data["is_editable"] = True
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update application status")
    
    # Get updated application
    updated_application = await get_application_by_id(db, application_id)
    
    return ApplicationResponse(
        id=str(updated_application.id),
        grant_id=updated_application.grant_id,
        applicant_name=updated_application.applicant_name,
        email=updated_application.email,
        proposal_title=updated_application.proposal_title,
        status=updated_application.status,
        submission_date=updated_application.submission_date,
        review_comments=updated_application.review_comments,
        biodata=updated_application.biodata,
        deadline=updated_application.deadline,
        is_editable=updated_application.is_editable,
        proposal_file_name=updated_application.proposal_file_name,
        proposal_file_size=updated_application.proposal_file_size,
        proposal_file_type=updated_application.proposal_file_type
    )

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
    
    return ApplicationResponse(
        id=str(updated_application.id),
        grant_id=updated_application.grant_id,
        applicant_name=updated_application.applicant_name,
        email=updated_application.email,
        proposal_title=updated_application.proposal_title,
        status=updated_application.status,
        submission_date=updated_application.submission_date,
        review_comments=updated_application.review_comments,
        biodata=updated_application.biodata,
        deadline=updated_application.deadline,
        proposal_file_name=updated_application.proposal_file_name
    )




@router.get("/{application_id}/document/{filename}")
async def download_application_document(
    application_id: str,
    filename: str,
    current_user = Depends(get_current_active_user)
):
    """Download application document stored as base64 in MongoDB"""
    db = await get_database()
    application = await get_application_by_id(db, application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check permissions - only grants managers, reviewers, and the applicant can download
    if (current_user.role not in ["Grants Manager", "Admin"] and 
        current_user.email != application.email):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify the filename matches the application's proposal file
    if application.proposal_file_name != filename:
        raise HTTPException(status_code=404, detail="Document not found for this application")
    
    # Check if file data exists in database
    if not application.proposal_file_data:
        raise HTTPException(status_code=404, detail="File data not found in database")
    
    try:
        # Decode base64 file data
        file_bytes = base64.b64decode(application.proposal_file_data)
        
        # Determine media type
        media_type = application.proposal_file_type or 'application/octet-stream'
        
        # Return the file as a response
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_bytes))
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding file data: {str(e)}")