from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class Milestone(BaseModel):
    id: str
    title: str
    due_date: str = Field(alias="dueDate")
    status: str  # pending, in_progress, completed, on_hold
    description: str
    progress_report_uploaded: Optional[bool] = Field(False, alias="progressReportUploaded")
    progress_report_date: Optional[str] = Field(None, alias="progressReportDate")
    progress_report_filename: Optional[str] = Field(None, alias="progressReportFilename")
    is_overdue: Optional[bool] = Field(False, alias="isOverdue")
    
    class Config:
        allow_population_by_field_name = True

class Requisition(BaseModel):
    id: str
    milestone_id: str = Field(alias="milestoneId")
    amount: float
    requested_date: str = Field(alias="requestedDate")
    status: str  # submitted, approved, rejected
    notes: str
    reviewed_by: Optional[str] = Field(None, alias="reviewedBy")
    reviewed_date: Optional[str] = Field(None, alias="reviewedDate")
    review_notes: Optional[str] = Field(None, alias="reviewNotes")
    
    class Config:
        allow_population_by_field_name = True

class Partner(BaseModel):
    id: str
    name: str
    role: str
    mou_filename: Optional[str] = Field(None, alias="mouFilename")
    uploaded_date: Optional[str] = Field(None, alias="uploadedDate")
    
    class Config:
        allow_population_by_field_name = True

class FinalReport(BaseModel):
    narrative_report: Optional[Dict[str, str]] = Field(None, alias="narrativeReport")  # filename, uploaded_date
    financial_report: Optional[Dict[str, str]] = Field(None, alias="financialReport")  # filename, uploaded_date
    status: str = "draft"  # draft, submitted, under_review, approved, revision_required
    submitted_date: Optional[str] = Field(None, alias="submittedDate")
    reviewed_by: Optional[str] = Field(None, alias="reviewedBy")
    reviewed_date: Optional[str] = Field(None, alias="reviewedDate")
    review_notes: Optional[str] = Field(None, alias="reviewNotes")
    
    class Config:
        allow_population_by_field_name = True

class ClosureWorkflow(BaseModel):
    status: str = "pending"  # pending, vc_review, signed_off, closed
    vc_sign_off_token: Optional[str] = Field(None, alias="vcSignOffToken")
    vc_signed_by: Optional[str] = Field(None, alias="vcSignedBy")
    vc_signed_date: Optional[str] = Field(None, alias="vcSignedDate")
    vc_notes: Optional[str] = Field(None, alias="vcNotes")
    closure_certificate_generated: Optional[bool] = Field(False, alias="closureCertificateGenerated")
    closure_certificate_date: Optional[str] = Field(None, alias="closureCertificateDate")
    
    class Config:
        allow_population_by_field_name = True

class Project(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    application_id: str = Field(alias="applicationId")
    title: str
    status: str = "active"  # active, completed, on_hold, cancelled, closed
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    milestones: List[Milestone] = []
    requisitions: List[Requisition] = []
    partners: List[Partner] = []
    final_report: Optional[FinalReport] = Field(None, alias="finalReport")
    closure_workflow: Optional[ClosureWorkflow] = Field(None, alias="closureWorkflow")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}