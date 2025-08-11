from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class ReviewerFeedback(BaseModel):
    id: str
    applicationId: str
    reviewerEmail: str
    reviewerName: Optional[str] = None
    comments: str
    decision: str  # 'approve' | 'reject' | 'request_changes'
    annotatedFileName: Optional[str] = None
    submittedAt: str
    reviewToken: str

class SignOffApproval(BaseModel):
    id: str
    applicationId: str
    role: str  # 'DORI' | 'DVC' | 'VC'
    approverEmail: str
    approverName: Optional[str] = None
    status: str  # 'pending' | 'approved' | 'rejected'
    comments: Optional[str] = None
    approvedAt: Optional[str] = None
    signOffToken: str

class ResearcherBiodata(BaseModel):
    name: str
    age: int
    email: str
    firstTimeApplicant: bool

class Application(BaseModel):
    """Application model matching frontend JSON structure exactly"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    grant_id: str = Field(alias="grantId")
    applicant_name: str = Field(alias="applicantName")
    email: str
    proposal_title: str = Field(alias="proposalTitle")
    institution: str = "Not specified"
    department: str = "Not specified"
    project_summary: str = Field(alias="projectSummary")
    objectives: str = "Research objectives"
    methodology: str = "Research methodology"
    expected_outcomes: str = Field(alias="expectedOutcomes")
    budget_amount: float = Field(alias="budgetAmount")
    budget_justification: str = Field(alias="budgetJustification")
    timeline: str = "12 months"
    status: str = "submitted"  # submitted, under_review, approved, rejected, withdrawn, editable, awaiting_signoff, signoff_complete, contract_pending, contract_received, needs_revision
    submission_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="submissionDate")
    review_comments: str = Field(default="", alias="reviewComments")
    biodata: Optional[dict[str, Any]] = None  # Match frontend ResearcherBiodata interface
    deadline: Optional[str] = None
    reviewer_feedback: List[ReviewerFeedback] = Field(default=[], alias="reviewerFeedback")
    final_decision: Optional[str] = Field(None, alias="finalDecision")
    decision_notes: Optional[str] = Field(None, alias="decisionNotes")
    is_editable: Optional[bool] = Field(None, alias="isEditable")
    assigned_reviewers: Optional[List[str]] = Field(None, alias="assignedReviewers")
    sign_off_approvals: Optional[List[SignOffApproval]] = Field(None, alias="signOffApprovals")
    award_amount: Optional[float] = Field(None, alias="awardAmount")
    contract_file_name: Optional[str] = Field(None, alias="contractFileName")
    award_letter_generated: Optional[bool] = Field(None, alias="awardLetterGenerated")
    revision_count: Optional[int] = Field(None, alias="revisionCount")
    original_submission_date: Optional[str] = Field(None, alias="originalSubmissionDate")
    proposal_file_name: Optional[str] = Field(None, alias="proposalFileName")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
