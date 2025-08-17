from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..utils.dependencies import get_current_active_user, get_database
from ..services.application_service import get_application_by_id
from ..models.application import ReviewHistoryEntry
import secrets
import string

router = APIRouter(prefix="/reviewers", tags=["reviewers"])

def generate_review_token() -> str:
    """Generate a secure review token"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

@router.post("/assign/{application_id}")
async def assign_reviewers(
    application_id: str,
    reviewer_data: dict,
    current_user = Depends(get_current_active_user)
):
    """Assign reviewers to an application (for grants managers and admins)"""
    db = await get_database()
    
    # Only grants managers and admins can assign reviewers
    if current_user.role not in ["Grants Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Only grants managers can assign reviewers")
    
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    reviewer_emails = reviewer_data.get("reviewer_emails", [])
    if not reviewer_emails:
        raise HTTPException(status_code=400, detail="At least one reviewer email is required")
    
    # Generate review tokens for each reviewer
    review_tokens = []
    for email in reviewer_emails:
        token = generate_review_token()
        review_tokens.append({
            "email": email,
            "token": token,
            "assigned_at": datetime.utcnow().isoformat()
        })
    
    # Update application with assigned reviewers and tokens
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {
            "$set": {
                "assigned_reviewers": reviewer_emails,
                "review_tokens": review_tokens
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to assign reviewers")
    
    return {
        "message": "Reviewers assigned successfully",
        "reviewer_count": len(reviewer_emails),
        "review_tokens": review_tokens
    }

@router.get("/application/{token}")
async def get_application_by_review_token(token: str):
    """Get application details by review token (for reviewers)"""
    db = await get_database()
    
    # Find application by review token
    application = await db.applications.find_one({
        "review_tokens.token": token
    })
    
    if not application:
        raise HTTPException(status_code=404, detail="Invalid review token or application not found")
    
    # Convert to Application model and return relevant fields
    from ..schemas.application import ApplicationResponse
    
    return ApplicationResponse(
        id=str(application["_id"]),
        grant_id=application.get("grant_id", ""),
        applicant_name=application.get("applicant_name", ""),
        email=application.get("email", ""),
        proposal_title=application.get("proposal_title", ""),
        status=application.get("status", ""),
        submission_date=application.get("submission_date", ""),
        review_comments=application.get("review_comments", ""),
        biodata=application.get("biodata"),
        deadline=application.get("deadline"),
        proposal_file_name=application.get("proposal_file_name")
    )

# Deprecated: Use /applications/{application_id}/review endpoint instead
# @router.post("/feedback/{application_id}")
# async def submit_reviewer_feedback(...):
#     """DEPRECATED: Use POST /applications/{application_id}/review instead"""
#     raise HTTPException(status_code=410, detail="Endpoint deprecated. Use POST /applications/{application_id}/review")

@router.get("/feedback/{application_id}")
async def get_reviewer_feedback(
    application_id: str,
    current_user = Depends(get_current_active_user)
):
    """Get all reviewer feedback for an application - Updated to use review_history"""
    db = await get_database()
    
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check permissions
    if current_user.role == "Researcher" and application.email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get application with review history
    app_data = await db.applications.find_one({"_id": ObjectId(application_id)})
    
    return {
        "application_id": application_id,
        "feedback": app_data.get("reviewHistory", [])
    }
