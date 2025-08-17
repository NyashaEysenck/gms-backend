from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.application import Application, ReviewHistoryEntry
from ..schemas.application import ApplicationCreate, ApplicationUpdate, ReviewHistoryEntryCreate
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

async def create_application(db: AsyncIOMotorDatabase, application_data: ApplicationCreate) -> Application:
    # Convert ApplicationCreate to dict using aliases (field names that match frontend)
    application_dict = application_data.dict(by_alias=True)
    
    # Add default values for required fields that might be missing
    application_dict.setdefault("submissionDate", datetime.utcnow().isoformat())
    application_dict.setdefault("reviewComments", "")
    application_dict.setdefault("status", "submitted")
    
    # Initialize empty arrays for fields that might be missing
    application_dict.setdefault("reviewHistory", [])
    application_dict.setdefault("signOffApprovals", [])
    
    # Set default values for optional fields
    application_dict.setdefault("revisionCount", 0)
    application_dict.setdefault("isEditable", False)
    application_dict.setdefault("awardAmount", None)
    application_dict.setdefault("contractFileName", None)
    application_dict.setdefault("awardLetterGenerated", False)
    application_dict.setdefault("originalSubmissionDate", application_dict.get("submissionDate"))
    
    # Insert into database
    result = await db.applications.insert_one(application_dict)
    application_dict["_id"] = result.inserted_id
    
    # Create Application model using by_alias=True to match field names
    return Application.parse_obj(application_dict)

async def get_application_by_id(db: AsyncIOMotorDatabase, application_id: str) -> Optional[Application]:
    if not ObjectId.is_valid(application_id):
        return None
    application = await db.applications.find_one({"_id": ObjectId(application_id)})
    if application:
        return Application.parse_obj(application)
    return None

async def get_all_applications(db: AsyncIOMotorDatabase) -> List[Application]:
    applications = []
    async for application_doc in db.applications.find():
        try:
            # Ensure required fields exist with defaults
            application_doc.setdefault("reviewHistory", [])
            application_doc.setdefault("signOffApprovals", [])
            application_doc.setdefault("revisionCount", 0)
            application_doc.setdefault("isEditable", False)
            
            application = Application.parse_obj(application_doc)
            applications.append(application)
        except Exception as e:
            print(f"Error parsing application document: {e}")
            print(f"Document: {application_doc}")
            continue
    return applications

async def get_applications_by_user(db: AsyncIOMotorDatabase, email: str) -> List[Application]:
    applications = []
    async for application in db.applications.find({"email": email}):
        applications.append(Application.parse_obj(application))
    return applications

async def get_applications_by_status(db: AsyncIOMotorDatabase, status: str) -> List[Application]:
    applications = []
    async for application in db.applications.find({"status": status}):
        applications.append(Application.parse_obj(application))
    return applications

async def get_applications_by_grant_call(db: AsyncIOMotorDatabase, grant_call_id: str) -> List[Application]:
    applications = []
    async for application in db.applications.find({"grant_call_id": grant_call_id}):
        applications.append(Application.parse_obj(application))
    return applications

async def update_application(db: AsyncIOMotorDatabase, application_id: str, application_update: ApplicationUpdate) -> Optional[Application]:
    if not ObjectId.is_valid(application_id):
        return None
    
    # Use alias field names to keep DB keys consistent with API (camelCase)
    update_data = application_update.dict(by_alias=True, exclude_none=True)
    if not update_data:
        return None
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)}, 
        {"$set": update_data}
    )
    
    if result.modified_count:
        return await get_application_by_id(db, application_id)
    return None

async def add_review_comment(db: AsyncIOMotorDatabase, application_id: str, review_data: ReviewHistoryEntryCreate, new_status: str) -> Optional[Application]:
    if not ObjectId.is_valid(application_id):
        return None
    
    # Create review history entry with generated ID and timestamp
    review_entry = {
        "id": f"rev_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "reviewerName": review_data.reviewer_name,
        "reviewerEmail": review_data.reviewer_email,
        "comments": review_data.comments,
        "submittedAt": datetime.utcnow().isoformat(),
        "status": new_status
    }
    
    # Update application with new review entry, latest comment, and status
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {
            "$push": {"reviewHistory": review_entry},
            "$set": {
                "reviewComments": review_data.comments,
                "status": new_status,
                "updated_at": datetime.utcnow(),
                "isEditable": new_status in ["needs_revision", "editable"]
            }
        }
    )
    
    if result.modified_count:
        return await get_application_by_id(db, application_id)
    return None

async def update_application_status(db: AsyncIOMotorDatabase, application_id: str, status: str, decision_notes: str = None) -> Optional[Application]:
    if not ObjectId.is_valid(application_id):
        return None
    
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if decision_notes:
        update_data["reviewComments"] = decision_notes
        update_data["final_decision"] = status
    
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return await get_application_by_id(db, application_id)
    return None

async def delete_application(db: AsyncIOMotorDatabase, application_id: str) -> bool:
    if not ObjectId.is_valid(application_id):
        return False
    result = await db.applications.delete_one({"_id": ObjectId(application_id)})
    return result.deleted_count > 0