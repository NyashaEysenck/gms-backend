from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .db_config import connect_to_mongo, close_mongo_connection, get_database
from .api import auth, users, applications, admin, reviewers, grant_calls, projects
from .config import settings
from .utils.error_handlers import (
    AuthenticationError,
    authentication_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from datetime import datetime
import secrets
import hashlib

app = FastAPI(
    title="Grants Management System API",
    description="Backend API for managing grant applications, projects, and funding workflows",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)

# Add exception handlers
app.add_exception_handler(AuthenticationError, authentication_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(applications.router)
app.include_router(admin.router)
app.include_router(reviewers.router)
app.include_router(grant_calls.router)
app.include_router(projects.router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    await load_sample_data_if_empty()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Grants Management System API", "version": "1.0.0"}

async def load_sample_data_if_empty():
    """Load sample data if database is empty"""
    try:
        db = await get_database()
        
        # Check if users collection is empty
        user_count = await db.users.count_documents({})
        if user_count > 0:
            print("Database already contains data, skipping sample data loading")
            return
        
        print("Loading sample data to empty database...")
        
        # 1. Load Users
        users_data = [
            {
                "email": "researcher@grants.edu",
                "password": hashlib.sha256("research123".encode()).hexdigest(),
                "role": "Researcher",
                "name": "Dr. Sarah Johnson",
                "createdAt": datetime.utcnow().isoformat()
            },
            {
                "email": "manager@grants.edu", 
                "password": hashlib.sha256("manager123".encode()).hexdigest(),
                "role": "Grants Manager",
                "name": "Michael Chen",
                "createdAt": datetime.utcnow().isoformat()
            },
            {
                "email": "admin@grants.edu",
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "role": "Admin",
                "name": "Lisa Rodriguez",
                "createdAt": datetime.utcnow().isoformat()
            }
        ]
        await db.users.insert_many(users_data)
        
        # 2. Load Grant Calls
        grant_calls_data = [
            {
                "id": "grant_001",
                "title": "Research Innovation Grant 2024",
                "description": "Supporting innovative research projects in technology and science",
                "status": "Open",
                "deadline": "2024-12-31T23:59:59Z",
                "fundingAmount": 500000,
                "eligibilityCriteria": "Open to all researchers with PhD",
                "applicationGuidelines": "Submit proposal with budget and timeline",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            },
            {
                "id": "grant_002", 
                "title": "Healthcare Innovation Fund",
                "description": "Advancing healthcare through innovative research",
                "status": "Open",
                "deadline": "2024-11-30T23:59:59Z",
                "fundingAmount": 750000,
                "eligibilityCriteria": "Healthcare researchers and institutions",
                "applicationGuidelines": "Focus on patient impact and clinical relevance",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
        ]
        await db.grant_calls.insert_many(grant_calls_data)
        
        # 3. Load Sample Applications
        applications_data = [
            {
                "grantId": "grant_001",
                "applicantName": "Dr. Sarah Johnson",
                "email": "researcher@grants.edu",
                "proposalTitle": "AI-Powered Climate Change Prediction Models",
                "institution": "University of Technology",
                "department": "Computer Science",
                "projectSummary": "Developing advanced AI models to predict climate change patterns with improved accuracy",
                "objectives": "Create predictive models for climate change analysis",
                "methodology": "Machine learning algorithms with historical climate data",
                "expectedOutcomes": "Improved climate prediction accuracy by 25%",
                "budgetAmount": 500000.0,
                "budgetJustification": "Equipment, personnel, and computational resources",
                "timeline": "24 months",
                "status": "approved",
                "submissionDate": "2024-07-15T10:30:00Z",
                "reviewComments": "Excellent proposal with strong methodology",
                "deadline": "2024-12-31T23:59:59Z",
                "revisionCount": 0,
                "originalSubmissionDate": "2024-07-15T10:30:00Z",
                "isEditable": False,
                "proposalFileName": "ai-climate-prediction.pdf",
                "proposalFileSize": 2048000,
                "proposalFileType": "application/pdf",
                "biodata": {
                    "name": "Dr. Sarah Johnson",
                    "age": 42,
                    "email": "researcher@grants.edu",
                    "firstTimeApplicant": False
                },
                "reviewHistory": [
                    {
                        "id": "rev_001",
                        "reviewerName": "Dr. Review Expert",
                        "reviewerEmail": "reviewer@grants.edu", 
                        "comments": "Strong technical approach and clear objectives",
                        "submittedAt": "2024-07-20T14:30:00Z",
                        "status": "approved"
                    }
                ],
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
        ]
        await db.applications.insert_many(applications_data)
        
        # 4. Load Sample Projects
        projects_data = [
            {
                "id": "proj_001",
                "applicationId": "app_001",
                "title": "AI Climate Prediction Implementation",
                "description": "Implementation phase of the AI climate prediction research",
                "status": "active",
                "startDate": "2024-08-01T00:00:00Z",
                "endDate": "2025-07-31T23:59:59Z",
                "budget": 500000,
                "principalInvestigator": "Dr. Sarah Johnson",
                "teamMembers": ["Dr. Sarah Johnson", "Research Assistant A"],
                "milestones": [
                    {
                        "id": "milestone_001",
                        "title": "Data Collection Phase",
                        "description": "Collect and prepare climate data",
                        "dueDate": "2024-10-31T23:59:59Z",
                        "status": "in_progress",
                        "completionPercentage": 60
                    }
                ],
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
        ]
        await db.projects.insert_many(projects_data)
        
        print("✅ Sample data loaded successfully")
        
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}