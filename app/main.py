from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import connect_to_mongo, close_mongo_connection
from .api import auth, users, grant_calls, applications, projects, documents
from .config import settings

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
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(grant_calls.router)
app.include_router(applications.router)
app.include_router(projects.router)
app.include_router(documents.router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Grants Management System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}