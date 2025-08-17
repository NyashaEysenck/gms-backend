import asyncio
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def load_data_from_json():
    """Clears collections and loads all frontend JSON data into MongoDB."""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    frontend_data_dir = "data"
    if not os.path.isdir(frontend_data_dir):
        # Adjust path for when called from API route
        frontend_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

    try:
        # 1. Clear collections
        await db.users.delete_many({})
        await db.grant_calls.delete_many({})
        await db.applications.delete_many({})
        await db.projects.delete_many({})

        # 2. Load Users
        with open(os.path.join(frontend_data_dir, "users.json"), "r") as f:
            users_data = json.load(f)
        users_to_insert = []
        for user in users_data["users"]:
            user_doc = user.copy()
            user_doc["hashed_password"] = pwd_context.hash(user["password"])
            users_to_insert.append(user_doc)
        if users_to_insert:
            await db.users.insert_many(users_to_insert)

        # 3. Load Grant Calls
        with open(os.path.join(frontend_data_dir, "grantCalls.json"), "r") as f:
            grant_calls_data = json.load(f)
        if grant_calls_data.get("grantCalls"):
            await db.grant_calls.insert_many(grant_calls_data["grantCalls"])

        # 4. Load Applications (with data structure transformation)
        with open(os.path.join(frontend_data_dir, "applications.json"), "r") as f:
            applications_data = json.load(f)
        
        if applications_data.get("applications"):
            # Transform applications to match new data structure
            applications_to_insert = []
            for app in applications_data["applications"]:
                app_doc = app.copy()
                
                # Transform reviewerFeedback to reviewHistory
                if "reviewerFeedback" in app_doc:
                    review_history = []
                    for feedback in app_doc["reviewerFeedback"]:
                        # Transform old feedback structure to new review history entry
                        history_entry = {
                            "id": feedback.get("id", ""),
                            "reviewerName": feedback.get("reviewerName", ""),
                            "reviewerEmail": feedback.get("reviewerEmail", ""),
                            "comments": feedback.get("comments", ""),
                            "submittedAt": feedback.get("submittedAt", ""),
                            "status": feedback.get("decision", "under_review")  # Map decision to status
                        }
                        review_history.append(history_entry)
                    
                    app_doc["reviewHistory"] = review_history
                    # Remove old field
                    del app_doc["reviewerFeedback"]
                else:
                    app_doc["reviewHistory"] = []
                
                applications_to_insert.append(app_doc)
            
            await db.applications.insert_many(applications_to_insert)

        # 5. Load Projects
        with open(os.path.join(frontend_data_dir, "projects.json"), "r") as f:
            projects_data = json.load(f)
        if projects_data.get("projects"):
            await db.projects.insert_many(projects_data["projects"])

        # 6. Create indexes
        await db.users.create_index("email", unique=True)
        await db.applications.create_index("email")
        await db.applications.create_index("grantId")
        await db.applications.create_index("status")
        await db.grant_calls.create_index("id")
        await db.projects.create_index("applicationId")

        return {"message": "Database reset and loaded successfully."}
    except Exception as e:
        return {"error": f"Failed to load data: {str(e)}"}
    finally:
        client.close()
