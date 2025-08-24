from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class ReviewHistoryEntryCreate(BaseModel):
    reviewer_name: str = Field(alias="reviewerName")
    reviewer_email: EmailStr = Field(alias="reviewerEmail")
    comments: str
    status: str  # The new status being set
    
    class Config:
        allow_population_by_field_name = True

class SignOffApprovalCreate(BaseModel):
    application_id: str = Field(alias="applicationId")
    role: str  # DORI, DVC, VC
    approver_email: EmailStr = Field(alias="approverEmail")
    approver_name: Optional[str] = Field(None, alias="approverName")
    status: str = "pending"  # pending, approved, rejected
    comments: Optional[str] = None
    sign_off_token: str = Field(alias="signOffToken")
    
    class Config:
        allow_population_by_field_name = True

class ApplicationCreate(BaseModel):
    grantId: str
    applicantName: str
    email: EmailStr
    proposalTitle: str
    institution: str
    department: str
    projectSummary: str
    objectives: str
    methodology: str
    expectedOutcomes: str
    budgetAmount: float
    budgetJustification: str
    timeline: str
    biodata: Optional[Dict[str, Any]] = None
    deadline: Optional[str] = None
    proposalFileName: Optional[str] = None
    proposalFileData: Optional[str] = None
    proposalFileSize: Optional[int] = None
    proposalFileType: Optional[str] = None
    reviewHistory: List[ReviewHistoryEntryCreate] = Field(default_factory=list)
    signOffApprovals: List = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True

class ApplicationUpdate(BaseModel):
    proposalTitle: Optional[str] = None
    projectSummary: Optional[str] = None
    objectives: Optional[str] = None
    methodology: Optional[str] = None
    expectedOutcomes: Optional[str] = None
    budgetAmount: Optional[float] = None
    budgetJustification: Optional[str] = None
    timeline: Optional[str] = None
    biodata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    reviewComments: Optional[str] = None
    isEditable: Optional[bool] = None
    contractFileName: Optional[str] = None
    awardLetterGenerated: Optional[bool] = None
    revisionCount: Optional[int] = None
    originalSubmissionDate: Optional[str] = None
    proposalFileName: Optional[str] = None
    proposalFileData: Optional[str] = None
    proposalFileSize: Optional[int] = None
    proposalFileType: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

class ReviewHistoryEntryResponse(BaseModel):
    id: str
    reviewerName: str = Field(alias="reviewerName")
    reviewerEmail: EmailStr = Field(alias="reviewerEmail")
    comments: str
    submittedAt: str = Field(alias="submittedAt")
    status: str
    
    class Config:
        allow_population_by_field_name = True

class SignOffApprovalResponse(BaseModel):
    id: str
    applicationId: str = Field(alias="applicationId")
    role: str  # DORI, DVC, VC
    approverEmail: EmailStr = Field(alias="approverEmail")
    approverName: Optional[str] = Field(alias="approverName")
    status: str  # pending, approved, rejected
    comments: Optional[str] = None
    approvedAt: Optional[str] = Field(alias="approvedAt")
    signOffToken: str = Field(alias="signOffToken")
    
    class Config:
        allow_population_by_field_name = True

class SignoffWorkflowResponse(BaseModel):
    status: str  # pending, approved, rejected
    award_amount: Optional[float] = Field(alias="awardAmount")
    approvals: List[Dict[str, Any]] = Field(default_factory=list)
    initiated_by: Optional[str] = Field(alias="initiatedBy")
    initiated_at: Optional[str] = Field(alias="initiatedAt")
    
    class Config:
        allow_population_by_field_name = True

class ApplicationResponse(BaseModel):
    id: str
    grant_id: str = Field(alias="grantId")  # Match frontend field name
    applicant_name: str = Field(alias="applicantName")  # Match frontend field name
    email: EmailStr
    proposal_title: str = Field(alias="proposalTitle")  # Match frontend field name
    status: str  # submitted, under_review, manager_approved, rejected, withdrawn, editable, awaiting_signoff, signoff_approved, contract_pending, contract_received, needs_revision
    submission_date: str = Field(alias="submissionDate")  # Match frontend field name
    review_comments: str = Field(alias="reviewComments")
    biodata: Optional[Dict[str, Any]] = None
    deadline: Optional[str] = None
    is_editable: Optional[bool] = Field(alias="isEditable")
    reviewHistory: Optional[List[ReviewHistoryEntryResponse]] = Field(alias="reviewHistory")
    sign_off_approvals: Optional[List[SignOffApprovalResponse]] = Field(alias="signOffApprovals")
    award_amount: Optional[float] = Field(alias="awardAmount")  # Frontend expects this field
    contract_file_name: Optional[str] = Field(alias="contractFileName")
    award_letter_generated: Optional[bool] = Field(alias="awardLetterGenerated")
    revision_count: Optional[int] = Field(alias="revisionCount")
    original_submission_date: Optional[str] = Field(alias="originalSubmissionDate")
    proposal_file_name: Optional[str] = Field(alias="proposalFileName")
    proposal_file_size: Optional[int] = Field(alias="proposalFileSize")
    proposal_file_type: Optional[str] = Field(alias="proposalFileType")
    signoff_workflow: Optional[SignoffWorkflowResponse] = Field(alias="signoffWorkflow")
    
    class Config:
        allow_population_by_field_name = True