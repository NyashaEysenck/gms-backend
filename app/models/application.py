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

class ReviewHistoryEntry(BaseModel):
    id: str
    reviewerName: str
    reviewerEmail: str
    comments: str
    submittedAt: str
    status: str  # The status set when this review was submitted

class SignOffApproval(BaseModel):
    id: Optional[str] = None
    applicationId: Optional[str] = None
    role: Optional[str] = None  # 'DORI' | 'DVC' | 'VC'
    approverEmail: Optional[str] = None
    approverName: Optional[str] = None
    status: Optional[str] = None  # 'pending' | 'approved' | 'rejected'
    comments: Optional[str] = None
    approvedAt: Optional[str] = None
    signOffToken: Optional[str] = None

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
    project_summary: str = Field(default="Project summary to be provided", alias="projectSummary")
    objectives: str = "Research objectives"
    methodology: str = "Research methodology"
    expected_outcomes: str = Field(default="Expected research outcomes", alias="expectedOutcomes")
    budget_amount: float = Field(default=0.0, alias="budgetAmount")
    budget_justification: str = Field(default="Budget justification to be provided", alias="budgetJustification")
    timeline: str = "12 months"
    status: str = "submitted"  # submitted, under_review, approved, rejected, withdrawn, editable, awaiting_signoff, signoff_complete, contract_pending, contract_received, needs_revision
    submission_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), alias="submissionDate")
    review_comments: str = Field(default="", alias="reviewComments")
    biodata: Optional[dict[str, Any]] = None  # Match frontend ResearcherBiodata interface
    deadline: Optional[str] = None
    reviewHistory: List[ReviewHistoryEntry] = Field(default=[], alias="reviewHistory")
    final_decision: Optional[str] = Field(None, alias="finalDecision")
    decision_notes: Optional[str] = Field(None, alias="decisionNotes")
    is_editable: Optional[bool] = Field(None, alias="isEditable")
    sign_off_approvals: Optional[List[SignOffApproval]] = Field(None, alias="signOffApprovals")
    award_amount: Optional[float] = Field(None, alias="awardAmount")
    contract_file_name: Optional[str] = Field(None, alias="contractFileName")
    award_letter_generated: Optional[bool] = Field(None, alias="awardLetterGenerated")
    revision_count: Optional[int] = Field(None, alias="revisionCount")
    original_submission_date: Optional[str] = Field(None, alias="originalSubmissionDate")
    proposal_file_name: Optional[str] = Field(None, alias="proposalFileName")
    proposal_file_data: Optional[str] = Field(None, alias="proposalFileData")  # Base64 encoded file content
    proposal_file_size: Optional[int] = Field(None, alias="proposalFileSize")  # File size in bytes
    proposal_file_type: Optional[str] = Field(None, alias="proposalFileType")  # MIME type
    signoff_workflow: Optional[dict] = Field(None, alias="signoffWorkflow")  # Sign-off workflow data
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
