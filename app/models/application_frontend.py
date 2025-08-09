from pydantic import BaseModel
from typing import Optional, List

class ReviewerFeedback(BaseModel):
    """Exact match to frontend ReviewerFeedback interface"""
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
    """Exact match to frontend SignOffApproval interface"""
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
    """Exact match to frontend ResearcherBiodata interface"""
    name: str
    age: int
    email: str
    firstTimeApplicant: bool

class Application(BaseModel):
    """Exact match to frontend Application interface"""
    id: str
    grantId: str
    applicantName: str
    email: str
    proposalTitle: str
    status: str
    submissionDate: str
    reviewComments: str
    biodata: Optional[ResearcherBiodata] = None
    deadline: Optional[str] = None
    isEditable: Optional[bool] = None
    assignedReviewers: Optional[List[str]] = None
    reviewerFeedback: Optional[List[ReviewerFeedback]] = None
    signOffApprovals: Optional[List[SignOffApproval]] = None
    awardAmount: Optional[float] = None
    contractFileName: Optional[str] = None
    awardLetterGenerated: Optional[bool] = None
    revisionCount: Optional[int] = None
    originalSubmissionDate: Optional[str] = None
    proposalFileName: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
