from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId

from ...utils.dependencies import get_current_active_user, get_database
from ...schemas.application import ReviewHistoryEntryCreate, ApplicationResponse
from ...services.application_service import get_application_by_id
from .utils import build_application_response

router = APIRouter()

@router.post("/{application_id}/review", response_model=ApplicationResponse)
async def add_review_comment(
    application_id: str,
    review_data: ReviewHistoryEntryCreate,
    new_status: Optional[str] = Query(None),
    current_user = Depends(get_current_active_user)
):
    """Add review comment and optionally update status"""
    db = await get_database()
    
    # Debug logging
    print(f"DEBUG: Adding review to application {application_id}")
    print(f"DEBUG: Review data received: {review_data}")
    print(f"DEBUG: New status: {new_status}")
    
    # Get application
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    print(f"DEBUG: Found application: {application.id}")
    
    # Create review history entry
    review_entry = {
        "id": str(ObjectId()),
        "reviewerName": review_data.reviewer_name,
        "reviewerEmail": review_data.reviewer_email,
        "comments": review_data.comments,
        "submittedAt": datetime.utcnow().isoformat(),
        "status": new_status or application.status
    }
    
    print(f"DEBUG: Created review entry: {review_entry}")
    
    # Prepare update operation
    if new_status:
        update_data = {
            "$push": {"reviewHistory": review_entry},
            "$set": {"status": new_status}
        }
    else:
        update_data = {
            "$push": {"reviewHistory": review_entry}
        }
    
    print(f"DEBUG: Update data: {update_data}")
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        update_data
    )
    
    print(f"DEBUG: Update result - matched: {result.matched_count}, modified: {result.modified_count}")
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to add review comment")
    
    # Return updated application
    updated_application = await get_application_by_id(db, application_id)
    print(f"DEBUG: Updated application review history length: {len(updated_application.reviewHistory or [])}")
    return build_application_response(updated_application)
