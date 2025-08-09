from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class MilestoneCreate(BaseModel):
    title: str
    due_date: str = Field(alias="dueDate")
    description: str
    
    class Config:
        allow_population_by_field_name = True

class RequisitionCreate(BaseModel):
    milestone_id: str = Field(alias="milestoneId")
    amount: float
    notes: str
    
    class Config:
        allow_population_by_field_name = True

class PartnerCreate(BaseModel):
    name: str
    role: str
    
    class Config:
        allow_population_by_field_name = True

class ProjectCreate(BaseModel):
    application_id: str = Field(alias="applicationId")
    title: str
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    
    class Config:
        allow_population_by_field_name = True

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    
    class Config:
        allow_population_by_field_name = True

class MilestoneResponse(BaseModel):
    id: str
    title: str
    due_date: str = Field(alias="dueDate")
    status: str
    description: str
    progress_report_uploaded: bool = Field(alias="progressReportUploaded")
    progress_report_date: Optional[str] = Field(alias="progressReportDate")
    progress_report_filename: Optional[str] = Field(alias="progressReportFilename")
    is_overdue: bool = Field(alias="isOverdue")
    
    class Config:
        allow_population_by_field_name = True

class RequisitionResponse(BaseModel):
    id: str
    milestone_id: str = Field(alias="milestoneId")
    amount: float
    requested_date: str = Field(alias="requestedDate")
    status: str
    notes: str
    reviewed_by: Optional[str] = Field(alias="reviewedBy")
    reviewed_date: Optional[str] = Field(alias="reviewedDate")
    review_notes: Optional[str] = Field(alias="reviewNotes")
    
    class Config:
        allow_population_by_field_name = True

class PartnerResponse(BaseModel):
    id: str
    name: str
    role: str
    mou_filename: Optional[str] = Field(alias="mouFilename")
    uploaded_date: Optional[str] = Field(alias="uploadedDate")
    
    class Config:
        allow_population_by_field_name = True

class FinalReportResponse(BaseModel):
    narrative_report: Optional[Dict[str, str]] = Field(alias="narrativeReport")
    financial_report: Optional[Dict[str, str]] = Field(alias="financialReport")
    status: str
    submitted_date: Optional[str] = Field(alias="submittedDate")
    reviewed_by: Optional[str] = Field(alias="reviewedBy")
    reviewed_date: Optional[str] = Field(alias="reviewedDate")
    review_notes: Optional[str] = Field(alias="reviewNotes")
    
    class Config:
        allow_population_by_field_name = True

class ClosureWorkflowResponse(BaseModel):
    status: str
    vc_sign_off_token: Optional[str] = Field(alias="vcSignOffToken")
    vc_signed_by: Optional[str] = Field(alias="vcSignedBy")
    vc_signed_date: Optional[str] = Field(alias="vcSignedDate")
    vc_notes: Optional[str] = Field(alias="vcNotes")
    closure_certificate_generated: bool = Field(alias="closureCertificateGenerated")
    closure_certificate_date: Optional[str] = Field(alias="closureCertificateDate")
    
    class Config:
        allow_population_by_field_name = True

class ProjectResponse(BaseModel):
    id: str
    application_id: str = Field(alias="applicationId")
    title: str
    status: str
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    milestones: List[MilestoneResponse] = []
    requisitions: List[RequisitionResponse] = []
    partners: List[PartnerResponse] = []
    final_report: Optional[FinalReportResponse] = Field(alias="finalReport")
    closure_workflow: Optional[ClosureWorkflowResponse] = Field(alias="closureWorkflow")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    
    class Config:
        allow_population_by_field_name = True