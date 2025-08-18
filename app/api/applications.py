from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import FileResponse, Response
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import base64
from ..utils.dependencies import get_current_active_user, get_database, require_role
from ..schemas.application import ApplicationCreate, ApplicationUpdate, ReviewHistoryEntryCreate, ApplicationResponse
from ..services.application_service import (
    create_application,
    get_application_by_id,
    get_all_applications,
    get_applications_by_user,
    get_applications_by_status,
    get_applications_by_grant_call,
    update_application,
    add_review_comment,
    update_application_status,
    delete_application
)
router = APIRouter(prefix="/applications", tags=["applications"])

def build_application_response(application) -> ApplicationResponse:
    """Helper function to build consistent ApplicationResponse with all fields"""
    # Handle both dict and object types
    if isinstance(application, dict):
        return ApplicationResponse(
            id=str(application.get("_id", application.get("id", ""))),
            grant_id=application.get("grantId", application.get("grant_id", "")),
            applicant_name=application.get("applicantName", application.get("applicant_name", "")),
            email=application.get("email", ""),
            proposal_title=application.get("proposalTitle", application.get("proposal_title", "")),
            status=application.get("status", ""),
            submission_date=application.get("submissionDate", application.get("submission_date", "")),
            review_comments=application.get("reviewComments", application.get("review_comments", "")),
            biodata=application.get("biodata"),
            deadline=application.get("deadline"),
            proposal_file_name=application.get("proposalFileName", application.get("proposal_file_name")),
            proposal_file_size=application.get("proposalFileSize", application.get("proposal_file_size")),
            proposal_file_type=application.get("proposalFileType", application.get("proposal_file_type")),
            reviewHistory=application.get("reviewHistory", []),
            revision_count=application.get("revisionCount", application.get("revision_count")),
            original_submission_date=application.get("originalSubmissionDate", application.get("original_submission_date")),
            is_editable=application.get("isEditable", application.get("is_editable")),
            sign_off_approvals=application.get("signOffApprovals", application.get("sign_off_approvals")),
            award_amount=application.get("awardAmount", application.get("award_amount")),
            contract_file_name=application.get("contractFileName", application.get("contract_file_name")),
            award_letter_generated=application.get("awardLetterGenerated", application.get("award_letter_generated")),
            signoff_workflow=application.get("signoffWorkflow", application.get("signoff_workflow"))
        )
    else:
        # Handle object type (original code)
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
            proposal_file_type=application.proposal_file_type,
            reviewHistory=application.reviewHistory or [],
            revision_count=application.revision_count,
            original_submission_date=application.original_submission_date,
            is_editable=application.is_editable,
            sign_off_approvals=application.sign_off_approvals,
            award_amount=application.award_amount,
            contract_file_name=application.contract_file_name,
            award_letter_generated=application.award_letter_generated,
            signoff_workflow=application.signoff_workflow
        )

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

@router.put("/{application_id}/status", response_model=ApplicationResponse)
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
        "submitted", "under_review", "approved", "rejected", 
        "withdrawn", "editable", "needs_revision", "awaiting_signoff", 
        "signoff_complete", "contract_pending", "contract_received"
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

@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    status_data: dict,
    current_user = Depends(get_current_active_user)
):
    """Update application status"""
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

@router.post("/{application_id}/review", response_model=ApplicationResponse)
async def add_review_comment(
    application_id: str,
    review_data: ReviewHistoryEntryCreate,
    new_status: Optional[str] = Query(None),
    current_user = Depends(get_current_active_user)
):
    """Add review comment and optionally update status"""
    db = await get_database()
    
    # Get application
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Create review history entry
    review_entry = {
        "id": str(ObjectId()),
        "reviewerName": review_data.reviewer_name,
        "reviewerEmail": review_data.reviewer_email,
        "comments": review_data.comments,
        "submittedAt": datetime.utcnow().isoformat(),
        "status": new_status or application.status
    }
    
    # Update application with review entry and optionally new status
    # Use camelCase field name to match model alias and frontend expectations
    update_data = {"$push": {"reviewHistory": review_entry}}
    if new_status:
        update_data["$set"] = {"status": new_status}
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        update_data
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to add review comment")
    
    # Return updated application
    updated_application = await get_application_by_id(db, application_id)
    return build_application_response(updated_application)

@router.post("/{application_id}/signoff/initiate")
async def initiate_application_signoff(
    application_id: str,
    signoff_data: dict,
    current_user = Depends(require_role("Grants Manager"))
):
    """Initiate sign-off workflow for an approved application"""
    db = await get_database()
    
    # Get application
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != "approved":
        raise HTTPException(status_code=400, detail="Application must be approved to initiate sign-off")
    
    from datetime import datetime
    import secrets
    
    # Create sign-off tokens for each approver
    sign_off_tokens = []
    approvals = []
    
    for approver in signoff_data.get("approvers", []):
        token = secrets.token_urlsafe(32)
        sign_off_tokens.append({
            "role": approver["role"],
            "token": token,
            "email": approver["email"]
        })
        
        approvals.append({
            "role": approver["role"],
            "email": approver["email"],
            "name": approver.get("name", ""),
            "approverName": approver.get("name", ""),  # Add for frontend compatibility
            "token": token,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        })
    
    # Update application with sign-off workflow
    update_data = {
        "signoff_workflow": {
            "status": "pending",
            "award_amount": signoff_data.get("award_amount", 0),
            "approvals": approvals,
            "initiated_by": current_user.email,
            "initiated_at": datetime.utcnow().isoformat()
        },
        "updated_at": datetime.utcnow()
    }
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to initiate sign-off workflow")
    
    return {
        "message": "Sign-off workflow initiated successfully",
        "sign_off_tokens": sign_off_tokens
    }

@router.get("/signoff/{token}")
async def get_application_by_signoff_token(token: str):
    """Get application and approval details by sign-off token"""
    db = await get_database()
    
    # Find application with this sign-off token
    application = await db.applications.find_one({
        "signoff_workflow.approvals.token": token
    })
    
    if not application:
        raise HTTPException(status_code=404, detail="Invalid or expired sign-off token")
    
    # Find the specific approval for this token
    approval = None
    signoff_workflow = application.get("signoff_workflow", {})
    for app_approval in signoff_workflow.get("approvals", []):
        if app_approval.get("token") == token:
            approval = app_approval
            break
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found for token")

    # Manually add award_amount to the top-level of the application dict
    # so build_application_response can find it.
    if "award_amount" in signoff_workflow:
        application["award_amount"] = signoff_workflow["award_amount"]

    # Convert application to response format
    app_response = build_application_response(application)
    
    return {
        "application": app_response,
        "approval": approval
    }

@router.post("/signoff/{token}")
async def submit_signoff_approval(
    token: str,
    submission: dict
):
    """Submit sign-off approval/rejection"""
    db = await get_database()
    
    # Find application with this sign-off token
    application = await db.applications.find_one({
        "signoff_workflow.approvals.token": token
    })
    
    if not application:
        raise HTTPException(status_code=404, detail="Invalid or expired sign-off token")
    
    from datetime import datetime
    
    # Update the specific approval
    result = await db.applications.update_one(
        {"_id": application["_id"], "signoff_workflow.approvals.token": token},
        {
            "$set": {
                "signoff_workflow.approvals.$.status": submission["decision"],
                "signoff_workflow.approvals.$.comments": submission.get("comments", ""),
                "signoff_workflow.approvals.$.approver_name": submission.get("approver_name", ""),
                "signoff_workflow.approvals.$.approved_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to submit approval")
    
    # Check if all approvals are complete
    updated_application = await db.applications.find_one({"_id": application["_id"]})
    approvals = updated_application.get("signoff_workflow", {}).get("approvals", [])
    
    all_approved = all(approval.get("status") == "approved" for approval in approvals)
    any_rejected = any(approval.get("status") == "rejected" for approval in approvals)
    
    # Update overall workflow status
    if any_rejected:
        workflow_status = "rejected"
    elif all_approved:
        workflow_status = "approved"
    else:
        workflow_status = "pending"
    
    await db.applications.update_one(
        {"_id": application["_id"]},
        {"$set": {"signoff_workflow.status": workflow_status}}
    )
    
    return {
        "message": "Sign-off approval submitted successfully",
        "application": build_application_response(updated_application)
    }

@router.get("/{application_id}/signoff/status")
async def get_signoff_status(
    application_id: str,
    current_user = Depends(get_current_active_user)
):
    """Get sign-off status for an application"""
    db = await get_database()
    
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    signoff_workflow = application.signoff_workflow or {}
    approvals = signoff_workflow.get("approvals", [])
    
    completed_approvals = sum(1 for approval in approvals if approval.get("status") in ["approved", "rejected"])
    total_approvals = len(approvals)
    current_status = signoff_workflow.get("status", "Not initiated")
    
    return {
        "current_status": current_status,
        "completed_approvals": completed_approvals,
        "total_approvals": total_approvals
    }
