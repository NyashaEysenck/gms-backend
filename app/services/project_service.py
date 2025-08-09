from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.project import Project, Milestone, Requisition, Partner, FinalReport, ClosureWorkflow
from typing import Optional, List
from bson import ObjectId
from datetime import datetime
import secrets

async def create_project(db: AsyncIOMotorDatabase, application_id: str, title: str, start_date: str, end_date: str) -> Project:
    project_data = {
        "application_id": application_id,
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "status": "active",
        "milestones": [],
        "requisitions": [],
        "partners": []
    }
    
    result = await db.projects.insert_one(project_data)
    project_data["_id"] = result.inserted_id
    return Project(**project_data)

async def get_project_by_id(db: AsyncIOMotorDatabase, project_id: str) -> Optional[Project]:
    if not ObjectId.is_valid(project_id):
        return None
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if project:
        return Project(**project)
    return None

async def get_all_projects(db: AsyncIOMotorDatabase) -> List[Project]:
    projects = []
    async for project in db.projects.find():
        projects.append(Project(**project))
    return projects

async def get_projects_by_user(db: AsyncIOMotorDatabase, user_email: str) -> List[Project]:
    # First get approved applications for this user
    approved_applications = []
    async for app in db.applications.find({"email": user_email, "status": "approved"}):
        approved_applications.append(str(app["_id"]))
    
    # Then get projects for those applications
    projects = []
    async for project in db.projects.find({"application_id": {"$in": approved_applications}}):
        projects.append(Project(**project))
    return projects

async def update_project_status(db: AsyncIOMotorDatabase, project_id: str, status: str) -> Optional[Project]:
    if not ObjectId.is_valid(project_id):
        return None
    
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        return await get_project_by_id(db, project_id)
    return None

async def add_milestone(db: AsyncIOMotorDatabase, project_id: str, milestone: Milestone) -> Optional[Project]:
    if not ObjectId.is_valid(project_id):
        return None
    
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$push": {"milestones": milestone.dict()}, "$set": {"updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        return await get_project_by_id(db, project_id)
    return None

async def submit_requisition(db: AsyncIOMotorDatabase, project_id: str, requisition_data: dict) -> Optional[Project]:
    if not ObjectId.is_valid(project_id):
        return None
    
    requisition = Requisition(
        id=f"req_{secrets.token_hex(8)}",
        milestone_id=requisition_data["milestone_id"],
        amount=requisition_data["amount"],
        requested_date=datetime.utcnow().isoformat(),
        status="submitted",
        notes=requisition_data["notes"]
    )
    
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$push": {"requisitions": requisition.dict()}, "$set": {"updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        return await get_project_by_id(db, project_id)
    return None

async def add_partner(db: AsyncIOMotorDatabase, project_id: str, partner_data: dict) -> Optional[Project]:
    if not ObjectId.is_valid(project_id):
        return None
    
    partner = Partner(
        id=f"partner_{secrets.token_hex(8)}",
        name=partner_data["name"],
        role=partner_data["role"]
    )
    
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$push": {"partners": partner.dict()}, "$set": {"updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        return await get_project_by_id(db, project_id)
    return None

async def upload_progress_report(db: AsyncIOMotorDatabase, project_id: str, milestone_id: str, filename: str) -> Optional[Project]:
    if not ObjectId.is_valid(project_id):
        return None
    
    result = await db.projects.update_one(
        {
            "_id": ObjectId(project_id),
            "milestones.id": milestone_id
        },
        {
            "$set": {
                "milestones.$.progress_report_uploaded": True,
                "milestones.$.progress_report_filename": filename,
                "milestones.$.progress_report_date": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return await get_project_by_id(db, project_id)
    return None

async def upload_final_report(db: AsyncIOMotorDatabase, project_id: str, report_type: str, filename: str) -> Optional[Project]:
    if not ObjectId.is_valid(project_id):
        return None
    
    update_field = f"final_report.{report_type}_report"
    
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                update_field: {
                    "filename": filename,
                    "uploaded_date": datetime.utcnow().isoformat()
                },
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return await get_project_by_id(db, project_id)
    return None

async def initiate_vc_signoff(db: AsyncIOMotorDatabase, project_id: str) -> Optional[str]:
    if not ObjectId.is_valid(project_id):
        return None
    
    token = f"vc_{project_id}_{secrets.token_hex(16)}"
    
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                "closure_workflow.status": "vc_review",
                "closure_workflow.vc_sign_off_token": token,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return token
    return None

async def get_project_by_vc_token(db: AsyncIOMotorDatabase, token: str) -> Optional[Project]:
    project = await db.projects.find_one({"closure_workflow.vc_sign_off_token": token})
    if project:
        return Project(**project)
    return None