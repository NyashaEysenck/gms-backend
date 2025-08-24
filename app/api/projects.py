from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from bson import ObjectId
from ..db_config import get_database
from ..services.project_service import (
    create_project, get_all_projects, get_project_by_id, get_projects_by_user,
    update_project_status, add_milestone, submit_requisition, add_partner,
    upload_progress_report, upload_final_report, initiate_vc_signoff, get_project_by_vc_token
)
from ..utils.dependencies import get_current_active_user, require_role
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    application_id: str
    title: str
    start_date: str
    end_date: str

class MilestoneCreate(BaseModel):
    title: str
    due_date: str
    description: str

class RequisitionCreate(BaseModel):
    milestone_id: str
    amount: float
    notes: str

class PartnerCreate(BaseModel):
    name: str
    role: str

class ProjectStatusUpdate(BaseModel):
    status: str

class VCSignOffSubmission(BaseModel):
    decision: str
    notes: str
    vc_name: str

class RequisitionStatusUpdate(BaseModel):
    status: str  # approved, rejected
    review_notes: str
    reviewed_by: str

@router.post("/")
async def create_new_project(
    project_data: ProjectCreate,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    project = await create_project(
        db, 
        project_data.application_id, 
        project_data.title, 
        project_data.start_date, 
        project_data.end_date
    )
    return {"id": str(project.id), "message": "Project created successfully"}

@router.get("/")
async def list_projects(current_user = Depends(get_current_active_user)):
    db = await get_database()
    
    if current_user.role == "Researcher":
        projects = await get_projects_by_user(db, current_user.email)
    else:
        projects = await get_all_projects(db)
    
    return [
        {
            "id": str(project.id),
            "applicationId": project.application_id,
            "title": project.title,
            "status": project.status,
            "startDate": project.start_date,
            "endDate": project.end_date,
            "milestones": [
                {
                    "id": m.id,
                    "title": m.title,
                    "dueDate": m.due_date,
                    "status": m.status,
                    "description": m.description,
                    "progressReportUploaded": m.progress_report_uploaded or False,
                    "progressReportDate": m.progress_report_date,
                    "progressReportFilename": m.progress_report_filename,
                    "isOverdue": m.is_overdue or False
                } for m in project.milestones
            ],
            "requisitions": [
                {
                    "id": r.id,
                    "milestoneId": r.milestone_id,
                    "amount": r.amount,
                    "requestedDate": r.requested_date,
                    "status": r.status,
                    "notes": r.notes,
                    "reviewedBy": r.reviewed_by,
                    "reviewedDate": r.reviewed_date,
                    "reviewNotes": r.review_notes
                } for r in project.requisitions
            ] if project.requisitions else [],
            "createdAt": project.created_at.isoformat(),
            "updatedAt": project.updated_at.isoformat()
        }
        for project in projects
    ]

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check access permissions for researchers
    if current_user.role == "Researcher":
        user_projects = await get_projects_by_user(db, current_user.email)
        if not any(p.id == project.id for p in user_projects):
            raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(project.id),
        "applicationId": project.application_id,
        "title": project.title,
        "status": project.status,
        "startDate": project.start_date,
        "endDate": project.end_date,
        "milestones": [
            {
                "id": m.id,
                "title": m.title,
                "dueDate": m.due_date,
                "status": m.status,
                "description": m.description,
                "progressReportUploaded": m.progress_report_uploaded or False,
                "progressReportDate": m.progress_report_date,
                "progressReportFilename": m.progress_report_filename,
                "isOverdue": m.is_overdue or False
            } for m in project.milestones
        ],
        "requisitions": [
            {
                "id": r.id,
                "milestoneId": r.milestone_id,
                "amount": r.amount,
                "requestedDate": r.requested_date,
                "status": r.status,
                "notes": r.notes,
                "reviewedBy": r.reviewed_by,
                "reviewedDate": r.reviewed_date,
                "reviewNotes": r.review_notes
            } for r in project.requisitions
        ] if project.requisitions else [],
        "partners": [
            {
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "mouFilename": p.mou_filename,
                "uploadedDate": p.uploaded_date
            } for p in project.partners
        ] if project.partners else [],
        "finalReport": {
            "narrativeReport": project.final_report.narrative_report,
            "financialReport": project.final_report.financial_report,
            "status": project.final_report.status,
            "submittedDate": project.final_report.submitted_date,
            "reviewedBy": project.final_report.reviewed_by,
            "reviewedDate": project.final_report.reviewed_date,
            "reviewNotes": project.final_report.review_notes
        } if project.final_report else None,
        "closureWorkflow": {
            "status": project.closure_workflow.status,
            "vcSignOffToken": project.closure_workflow.vc_sign_off_token,
            "vcSignedBy": project.closure_workflow.vc_signed_by,
            "vcSignedDate": project.closure_workflow.vc_signed_date,
            "vcNotes": project.closure_workflow.vc_notes,
            "closureCertificateGenerated": project.closure_workflow.closure_certificate_generated,
            "closureCertificateDate": project.closure_workflow.closure_certificate_date
        } if project.closure_workflow else None,
        "createdAt": project.created_at.isoformat(),
        "updatedAt": project.updated_at.isoformat()
    }

@router.patch("/{project_id}/status")
async def update_status(
    project_id: str,
    status_update: ProjectStatusUpdate,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    project = await update_project_status(db, project_id, status_update.status)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project status updated successfully"}

@router.post("/{project_id}/milestones")
async def add_project_milestone(
    project_id: str,
    milestone_data: MilestoneCreate,
    current_user = Depends(require_role("Grants Manager"))
):
    from ..models.project import Milestone
    import secrets
    
    db = await get_database()
    milestone = Milestone(
        id=f"milestone_{secrets.token_hex(8)}",
        title=milestone_data.title,
        due_date=milestone_data.due_date,
        status="pending",
        description=milestone_data.description
    )
    
    project = await add_milestone(db, project_id, milestone)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Milestone added successfully"}

@router.post("/{project_id}/requisitions")
async def submit_fund_requisition(
    project_id: str,
    requisition_data: RequisitionCreate,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    # Check if user has access to this project
    if current_user.role == "Researcher":
        user_projects = await get_projects_by_user(db, current_user.email)
        if not any(str(p.id) == project_id for p in user_projects):
            raise HTTPException(status_code=403, detail="Access denied")
    
    project = await submit_requisition(db, project_id, requisition_data.dict())
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Requisition submitted successfully"}

@router.post("/{project_id}/partners")
async def add_project_partner(
    project_id: str,
    partner_data: PartnerCreate,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    # Check if user has access to this project
    if current_user.role == "Researcher":
        user_projects = await get_projects_by_user(db, current_user.email)
        if not any(str(p.id) == project_id for p in user_projects):
            raise HTTPException(status_code=403, detail="Access denied")
    
    project = await add_partner(db, project_id, partner_data.dict())
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Partner added successfully"}

@router.post("/{project_id}/milestones/{milestone_id}/progress-report")
async def upload_milestone_progress_report(
    project_id: str,
    milestone_id: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    # Check if user has access to this project
    if current_user.role == "Researcher":
        user_projects = await get_projects_by_user(db, current_user.email)
        if not any(str(p.id) == project_id for p in user_projects):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, you would save the file to storage
    # For now, we'll just record the filename
    project = await upload_progress_report(db, project_id, milestone_id, file.filename)
    if not project:
        raise HTTPException(status_code=404, detail="Project or milestone not found")
    
    return {"message": "Progress report uploaded successfully"}

@router.post("/{project_id}/final-report/{report_type}")
async def upload_project_final_report(
    project_id: str,
    report_type: str,  # narrative or financial
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    if report_type not in ["narrative", "financial"]:
        raise HTTPException(status_code=400, detail="Report type must be 'narrative' or 'financial'")
    
    # Check if user has access to this project
    if current_user.role == "Researcher":
        user_projects = await get_projects_by_user(db, current_user.email)
        if not any(str(p.id) == project_id for p in user_projects):
            raise HTTPException(status_code=403, detail="Access denied")
    
    project = await upload_final_report(db, project_id, report_type, file.filename)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": f"{report_type.title()} report uploaded successfully"}

@router.post("/{project_id}/initiate-vc-signoff")
async def initiate_vc_sign_off(
    project_id: str,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    token = await initiate_vc_signoff(db, project_id)
    if not token:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "VC sign-off initiated", "token": token}

@router.get("/vc-signoff/{token}")
async def get_project_for_vc_signoff(token: str):
    db = await get_database()
    project = await get_project_by_vc_token(db, token)
    if not project:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    return {
        "id": str(project.id),
        "application_id": project.application_id,
        "title": project.title,
        "status": project.status,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "final_report": project.final_report,
        "closure_workflow": project.closure_workflow,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat()
    }

@router.post("/vc-signoff/{token}/submit")
async def submit_vc_sign_off(
    token: str,
    submission: VCSignOffSubmission
):
    db = await get_database()
    project = await get_project_by_vc_token(db, token)
    if not project:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Update project with VC decision
    from datetime import datetime
    
    update_data = {
        "closure_workflow.status": "signed_off" if submission.decision == "approved" else "rejected",
        "closure_workflow.vc_signed_by": submission.vc_name,
        "closure_workflow.vc_signed_date": datetime.utcnow().isoformat(),
        "closure_workflow.vc_notes": submission.notes,
        "updated_at": datetime.utcnow()
    }
    
    # If approved, also update project status
    if submission.decision == "approved":
        update_data["status"] = "completed"
    
    result = await db.projects.update_one(
        {"_id": project.id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update project")
    
    return {"message": "VC sign-off submitted successfully", "status": update_data["closure_workflow.status"]}

@router.put("/{project_id}/milestones/{milestone_id}")
async def update_milestone(
    project_id: str,
    milestone_id: str,
    milestone_update: dict,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    # Check if user has access to this project
    if current_user.role == "Researcher":
        user_projects = await get_projects_by_user(db, current_user.email)
        if not any(str(p.id) == project_id for p in user_projects):
            raise HTTPException(status_code=403, detail="Access denied")
    
    from datetime import datetime
    
    # Update milestone in project
    update_fields = {f"milestones.$.{k}": v for k, v in milestone_update.items()}
    update_fields["updated_at"] = datetime.utcnow()
    
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id), "milestones.id": milestone_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Project or milestone not found")
    
    return {"message": "Milestone updated successfully"}

@router.delete("/{project_id}/partners/{partner_id}")
async def remove_partner(
    project_id: str,
    partner_id: str,
    current_user = Depends(get_current_active_user)
):
    db = await get_database()
    
    # Check if user has access to this project
    if current_user.role == "Researcher":
        user_projects = await get_projects_by_user(db, current_user.email)
        if not any(str(p.id) == project_id for p in user_projects):
            raise HTTPException(status_code=403, detail="Access denied")
    
    from datetime import datetime
    
    # Remove partner from project
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$pull": {"partners": {"id": partner_id}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Project or partner not found")
    
    return {"message": "Partner removed successfully"}

@router.patch("/{project_id}/requisitions/{requisition_id}/status")
async def update_requisition_status(
    project_id: str,
    requisition_id: str,
    status_update: RequisitionStatusUpdate,
    current_user = Depends(require_role("Grants Manager"))
):
    db = await get_database()
    
    from datetime import datetime
    
    # Update requisition status in project
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id), "requisitions.id": requisition_id},
        {
            "$set": {
                "requisitions.$.status": status_update.status,
                "requisitions.$.review_notes": status_update.review_notes,
                "requisitions.$.reviewed_by": status_update.reviewed_by,
                "requisitions.$.reviewed_date": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Project or requisition not found")
    
    return {"message": f"Requisition {status_update.status} successfully"}