from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class ReviewerFeedbackCreate(BaseModel):
    application_id: str = Field(alias="applicationId")
    reviewer_email: EmailStr = Field(alias="reviewerEmail")
    reviewer_name: Optional[str] = Field(None, alias="reviewerName")
    comments: str
    decision: str  # approve, reject, request_changes
    annotated_file_name: Optional[str] = Field(None, alias="annotatedFileName")
    review_token: str = Field(alias="reviewToken")
    
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
    grant_id: str = Field(alias="grantId")  # Match frontend field name
    applicant_name: str = Field(alias="applicantName")  # Match frontend field name
    email: EmailStr
    proposal_title: str = Field(alias="proposalTitle")  # Match frontend field name
    institution: str = "Not specified"
    department: str = "Not specified"
    project_summary: str = Field(default="Project summary to be provided", alias="projectSummary")
    objectives: str = "Research objectives"
    methodology: str = "Research methodology"
    expected_outcomes: str = Field(default="Expected research outcomes", alias="expectedOutcomes")
    budget_amount: float = Field(default=0.0, alias="budgetAmount")
    budget_justification: str = Field(default="Budget justification to be provided", alias="budgetJustification")
    timeline: str = "12 months"
    biodata: Optional[Dict[str, Any]] = None  # Match frontend ResearcherBiodata interface
    deadline: Optional[str] = None
    proposal_file_name: Optional[str] = Field(None, alias="proposalFileName")
    
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
    assigned_reviewers: Optional[List[str]] = Field(None, alias="assignedReviewers")
    award_amount: Optional[float] = Field(None, alias="awardAmount")
    contract_file_name: Optional[str] = Field(None, alias="contractFileName")
    award_letter_generated: Optional[bool] = Field(None, alias="awardLetterGenerated")
    revision_count: Optional[int] = Field(None, alias="revisionCount")
    original_submission_date: Optional[str] = Field(None, alias="originalSubmissionDate")
    proposal_file_name: Optional[str] = Field(None, alias="proposalFileName")
    
    class Config:
        allow_population_by_field_name = True

class ReviewerFeedbackResponse(BaseModel):
    id: str
    application_id: str = Field(alias="applicationId")
    reviewer_email: EmailStr = Field(alias="reviewerEmail")
    reviewer_name: Optional[str] = Field(alias="reviewerName")
    comments: str
    decision: str  # approve, reject, request_changes
    annotated_file_name: Optional[str] = Field(alias="annotatedFileName")
    submitted_at: str = Field(alias="submittedAt")
    review_token: str = Field(alias="reviewToken")
    
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
    review_comments: str = Field(alias="reviewComments")  # Match frontend field name
    biodata: Optional[Dict[str, Any]] = None  # Match frontend ResearcherBiodata interface
    deadline: Optional[str] = None
    is_editable: Optional[bool] = Field(alias="isEditable")
    assigned_reviewers: Optional[List[str]] = Field(alias="assignedReviewers")
    reviewer_feedback: Optional[List[ReviewerFeedbackResponse]] = Field(alias="reviewerFeedback")
    sign_off_approvals: Optional[List[SignOffApprovalResponse]] = Field(alias="signOffApprovals")
    award_amount: Optional[float] = Field(alias="awardAmount")
    contract_file_name: Optional[str] = Field(alias="contractFileName")
    award_letter_generated: Optional[bool] = Field(alias="awardLetterGenerated")
    revision_count: Optional[int] = Field(alias="revisionCount")
    original_submission_date: Optional[str] = Field(alias="originalSubmissionDate")
    proposal_file_name: Optional[str] = Field(alias="proposalFileName")
    
    class Config:
        allow_population_by_field_name = True