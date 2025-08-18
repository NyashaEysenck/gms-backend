from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
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
            "application_id": project.application_id,
            "title": project.title,
            "status": project.status,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "milestones": project.milestones,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
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
        "application_id": project.application_id,
        "title": project.title,
        "status": project.status,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "milestones": project.milestones,
        "requisitions": project.requisitions,
        "partners": project.partners,
        "final_report": project.final_report,
        "closure_workflow": project.closure_workflow,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat()
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