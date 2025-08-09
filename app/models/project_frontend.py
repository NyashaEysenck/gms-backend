from pydantic import BaseModel
from typing import Optional, List

class Milestone(BaseModel):
    """Exact match to frontend Milestone structure"""
    id: str
    title: str
    dueDate: str
    status: str
    description: str
    progressReportUploaded: bool
    progressReportDate: Optional[str] = None
    progressReportFilename: Optional[str] = None

class Requisition(BaseModel):
    """Exact match to frontend Requisition structure"""
    id: str
    milestoneId: str
    amount: float
    requestedDate: str
    status: str
    notes: str
    reviewedBy: Optional[str] = None
    reviewedDate: Optional[str] = None
    reviewNotes: Optional[str] = None

class Partner(BaseModel):
    """Exact match to frontend Partner structure"""
    id: str
    name: str
    role: str
    mouFilename: Optional[str] = None
    uploadedDate: Optional[str] = None

class FinalReport(BaseModel):
    """Exact match to frontend FinalReport structure"""
    status: str
    submittedDate: Optional[str] = None
    filename: Optional[str] = None
    financialReport: Optional[str] = None
    reviewedBy: Optional[str] = None
    reviewedDate: Optional[str] = None
    reviewNotes: Optional[str] = None

class ClosureWorkflow(BaseModel):
    """Exact match to frontend ClosureWorkflow structure"""
    status: str
    vcSignOffToken: Optional[str] = None
    vcSignedBy: Optional[str] = None
    vcSignedDate: Optional[str] = None
    vcNotes: Optional[str] = None
    closureCertificateGenerated: bool = False
    closureCertificateDate: Optional[str] = None

class Project(BaseModel):
    """Exact match to frontend Project structure"""
    id: str
    applicationId: str
    title: str
    status: str
    startDate: str
    endDate: str
    milestones: List[Milestone] = []
    requisitions: List[Requisition] = []
    partners: List[Partner] = []
    finalReport: Optional[FinalReport] = None
    closureWorkflow: Optional[ClosureWorkflow] = None

    class Config:
        allow_population_by_field_name = True
