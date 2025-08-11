from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..database import get_database
from ..schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse, ReviewerFeedbackCreate
from ..services.application_service import (
    create_application, get_all_applications, get_application_by_id,
    get_applications_by_user, get_applications_by_status, get_applications_by_grant_call,
    update_application, add_reviewer_feedback, update_application_status, delete_application
)
from ..utils.dependencies import get_current_active_user, require_role

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
        grant_call_id=application.grant_id,
        title=application.proposal_title,
        email=application.email,
        researcher_name=application.applicant_name,
        institution=application.institution,
        department=application.department,
        project_summary=application.project_summary,
        objectives=application.objectives,
        methodology=application.methodology,
        expected_outcomes=application.expected_outcomes,
        budget_amount=application.budget_amount,
        budget_justification=application.budget_justification,
        timeline=application.timeline,
        status=application.status,
        submitted_at=application.submission_date,
        updated_at=application.updated_at.isoformat()
    )

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
            grant_call_id=application.grant_id,
            title=application.proposal_title,
            email=application.email,
            researcher_name=application.applicant_name,
            institution=application.institution,
            department=application.department,
            project_summary=application.project_summary,
            objectives=application.objectives,
            methodology=application.methodology,
            expected_outcomes=application.expected_outcomes,
            budget_amount=application.budget_amount,
            budget_justification=application.budget_justification,
            timeline=application.timeline,
            status=application.status,
            submitted_at=application.submission_date,
            updated_at=application.updated_at.isoformat()
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
        grant_call_id=application.grant_id,
        title=application.proposal_title,
        email=application.email,
        researcher_name=application.applicant_name,
        institution=application.institution,
        department=application.department,
        project_summary=application.project_summary,
        objectives=application.objectives,
        methodology=application.methodology,
        expected_outcomes=application.expected_outcomes,
        budget_amount=application.budget_amount,
        budget_justification=application.budget_justification,
        timeline=application.timeline,
        status=application.status,
        submitted_at=application.submission_date,
        updated_at=application.updated_at.isoformat()
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
        grant_call_id=updated_application.grant_id,
        title=updated_application.proposal_title,
        email=updated_application.email,
        researcher_name=updated_application.applicant_name,
        institution=updated_application.institution,
        department=updated_application.department,
        project_summary=updated_application.project_summary,
        objectives=updated_application.objectives,
        methodology=updated_application.methodology,
        expected_outcomes=updated_application.expected_outcomes,
        budget_amount=updated_application.budget_amount,
        budget_justification=updated_application.budget_justification,
        timeline=updated_application.timeline,
        status=updated_application.status,
        submitted_at=updated_application.submission_date,
        updated_at=updated_application.updated_at.isoformat()
    )

@router.post("/{application_id}/reviews")
async def submit_review(
    application_id: str,
    feedback_data: ReviewerFeedbackCreate,
    current_user = Depends(require_role("Reviewer"))
):
    db = await get_database()
    
    # Ensure reviewer is submitting their own feedback
    if feedback_data.reviewer_email != current_user.email:
        raise HTTPException(status_code=403, detail="Can only submit your own reviews")
    
    application = await add_reviewer_feedback(db, application_id, feedback_data)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Review submitted successfully"}

@router.patch("/{application_id}/status")
async def update_status(
    application_id: str,
    status: str,
    decision_notes: Optional[str] = None,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    application = await update_application_status(db, application_id, status, decision_notes)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Application status updated successfully"}

@router.delete("/{application_id}")
async def delete_application_endpoint(
    application_id: str,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    success = await delete_application(db, application_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Application deleted successfully"}