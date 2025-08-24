from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
import secrets

from ...utils.dependencies import get_current_active_user, get_database, require_role
from ...services.application_service import get_application_by_id
from .utils import build_application_response

router = APIRouter()

@router.post("/{application_id}/signoff/initiate")
async def initiate_application_signoff(
    application_id: str,
    signoff_data: dict,
    current_user = Depends(require_role("Grants Manager"))
):
    """Initiate sign-off workflow for a manager approved application"""
    db = await get_database()
    
    # Get application
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != "manager_approved":
        raise HTTPException(status_code=400, detail="Application must be manager approved to initiate sign-off")
    
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
    
    # Update overall workflow status and application status
    if any_rejected:
        workflow_status = "rejected"
        application_status = "rejected"
    elif all_approved:
        workflow_status = "approved"
        application_status = "signoff_approved"  # Set final approval status
    else:
        workflow_status = "pending"
        application_status = None  # Don't change application status if still pending
    
    # Update both workflow status and application status
    update_data = {"signoff_workflow.status": workflow_status}
    if application_status:
        update_data["status"] = application_status
        update_data["updated_at"] = datetime.utcnow()
    
    await db.applications.update_one(
        {"_id": application["_id"]},
        {"$set": update_data}
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
