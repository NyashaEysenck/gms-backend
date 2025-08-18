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
    grantId: str = Field(..., alias="grantId")
    applicantName: str = Field(..., alias="applicantName")
    email: EmailStr = Field(..., alias="email")
    proposalTitle: str = Field(..., alias="proposalTitle")
    institution: str = Field(..., alias="institution")
    department: str = Field(..., alias="department")
    projectSummary: str = Field(..., alias="projectSummary")
    objectives: str = Field(..., alias="objectives")
    methodology: str = Field(..., alias="methodology")
    expectedOutcomes: str = Field(..., alias="expectedOutcomes")
    budgetAmount: float = Field(..., alias="budgetAmount")
    budgetJustification: str = Field(..., alias="budgetJustification")
    timeline: str = Field(..., alias="timeline")
    biodata: Optional[Dict[str, Any]] = Field(None, alias="biodata")
    deadline: Optional[str] = None
    proposalFileName: Optional[str] = Field(None, alias="proposalFileName")
    proposalFileData: Optional[str] = Field(None, alias="proposalFileData")
    proposalFileSize: Optional[int] = Field(None, alias="proposalFileSize")
    proposalFileType: Optional[str] = Field(None, alias="proposalFileType")
    reviewHistory: List[ReviewHistoryEntryCreate] = Field(default_factory=list, alias="reviewHistory")
    signOffApprovals: List = Field(default_factory=list, alias="signOffApprovals")

    class Config:
        allow_population_by_field_name = True

class ApplicationUpdate(BaseModel):
    proposal_title: Optional[str] = Field(None, alias="proposalTitle")  # Match frontend field name
    project_summary: Optional[str] = Field(None, alias="projectSummary")
    objectives: Optional[str] = None
    methodology: Optional[str] = None
    expected_outcomes: Optional[str] = Field(None, alias="expectedOutcomes")
    budget_amount: Optional[float] = Field(None, alias="budgetAmount")
    budget_justification: Optional[str] = Field(None, alias="budgetJustification")
    timeline: Optional[str] = None
    biodata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    review_comments: Optional[str] = Field(None, alias="reviewComments")
    is_editable: Optional[bool] = Field(None, alias="isEditable")
    award_amount: Optional[float] = Field(None, alias="awardAmount")
    contract_file_name: Optional[str] = Field(None, alias="contractFileName")
    award_letter_generated: Optional[bool] = Field(None, alias="awardLetterGenerated")
    revision_count: Optional[int] = Field(None, alias="revisionCount")
    original_submission_date: Optional[str] = Field(None, alias="originalSubmissionDate")
    proposal_file_name: Optional[str] = Field(None, alias="proposalFileName")
    proposal_file_data: Optional[str] = Field(None, alias="proposalFileData")
    proposal_file_size: Optional[int] = Field(None, alias="proposalFileSize")
    proposal_file_type: Optional[str] = Field(None, alias="proposalFileType")
    
    class Config:
        allow_population_by_field_name = True

class ReviewHistoryEntryResponse(BaseModel):
    id: str
    reviewer_name: str = Field(alias="reviewerName")
    reviewer_email: EmailStr = Field(alias="reviewerEmail")
    comments: str
    submitted_at: str = Field(alias="submittedAt")
    status: str
    
    class Config:
        allow_population_by_field_name = True

class SignOffApprovalResponse(BaseModel):
    id: str
    application_id: str = Field(alias="applicationId")
    role: str  # DORI, DVC, VC
    approver_email: EmailStr = Field(alias="approverEmail")
    approver_name: Optional[str] = Field(alias="approverName")
    status: str  # pending, approved, rejected
    comments: Optional[str] = None
    approved_at: Optional[str] = Field(alias="approvedAt")
    sign_off_token: str = Field(alias="signOffToken")
    
    class Config:
        allow_population_by_field_name = True

class ApplicationResponse(BaseModel):
    id: str
    grant_id: str = Field(alias="grantId")  # Match frontend field name
    applicant_name: str = Field(alias="applicantName")  # Match frontend field name
    email: EmailStr
    proposal_title: str = Field(alias="proposalTitle")  # Match frontend field name
    status: str  # submitted, under_review, approved, rejected, withdrawn, editable, awaiting_signoff, signoff_complete, contract_pending, contract_received, needs_revision
    submission_date: str = Field(alias="submissionDate")  # Match frontend field name
    review_comments: str = Field(alias="reviewComments")
    biodata: Optional[Dict[str, Any]] = None
    deadline: Optional[str] = None
    is_editable: Optional[bool] = Field(alias="isEditable")
    reviewHistory: Optional[List[ReviewHistoryEntryResponse]] = Field(alias="reviewHistory")
    sign_off_approvals: Optional[List[SignOffApprovalResponse]] = Field(alias="signOffApprovals")
    award_amount: Optional[float] = Field(alias="awardAmount")
    contract_file_name: Optional[str] = Field(alias="contractFileName")
    award_letter_generated: Optional[bool] = Field(alias="awardLetterGenerated")
    revision_count: Optional[int] = Field(alias="revisionCount")
    original_submission_date: Optional[str] = Field(alias="originalSubmissionDate")
    proposal_file_name: Optional[str] = Field(alias="proposalFileName")
    proposal_file_size: Optional[int] = Field(alias="proposalFileSize")
    proposal_file_type: Optional[str] = Field(alias="proposalFileType")
    signoff_workflow: Optional[Dict[str, Any]] = Field(alias="signoffWorkflow")
    
    class Config:
        allow_population_by_field_name = True