#!/usr/bin/env python3
"""
Load frontend JSON data exactly as-is into MongoDB.
This preserves the exact frontend data structure without any transformations.
"""
import asyncio
import json
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def load_frontend_data():
    """Load all frontend JSON data exactly as-is into MongoDB."""
    print("🚀 Loading Frontend Data into MongoDB...")
    print(f"📍 Current working directory: {os.getcwd()}")
    print(f"📁 Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"📍 MongoDB URI: {settings.mongodb_uri}")
    print(f"📊 Database: {settings.database_name}")
    print()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    # Use absolute path for data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_data_dir = os.path.join(script_dir, "data")
    
    # Check if data directory exists
    if not os.path.exists(frontend_data_dir):
        print(f"❌ Data directory '{frontend_data_dir}' not found!")
        print(f"📁 Available files in script dir: {os.listdir(script_dir) if os.path.exists(script_dir) else 'Script dir not found'}")
        print(f"📁 Available files in current dir: {os.listdir('.') if os.path.exists('.') else 'Current dir not found'}")
        raise FileNotFoundError(f"Data directory '{frontend_data_dir}' not found")
    
    try:
        # 1. Load Users (with password hashing)
        print("👥 Loading users...")
        users_file = os.path.join(frontend_data_dir, "users.json")
        with open(users_file, "r") as f:
            users_data = json.load(f)
        
        # Clear existing users
        await db.users.delete_many({})
        
        # Process users - hash passwords but keep everything else exactly the same
        users_to_insert = []
        for user in users_data["users"]:
            user_doc = user.copy()  # Keep all original fields
            # Add hashed password for backend auth, but keep original password field too
            user_doc["hashed_password"] = pwd_context.hash(user["password"])
            users_to_insert.append(user_doc)
        
        result = await db.users.insert_many(users_to_insert)
        print(f"   ✅ Inserted {len(result.inserted_ids)} users")
        
        # 2. Load Grant Calls (exactly as-is)
        print("📋 Loading grant calls...")
        grant_calls_file = os.path.join(frontend_data_dir, "grantCalls.json")
        with open(grant_calls_file, "r") as f:
            grant_calls_data = json.load(f)
        
        # Clear existing grant calls
        await db.grant_calls.delete_many({})
        
        # Insert exactly as-is
        result = await db.grant_calls.insert_many(grant_calls_data["grantCalls"])
        print(f"   ✅ Inserted {len(result.inserted_ids)} grant calls")
        
        # 3. Load Applications (with data structure transformation)
        print("📝 Loading applications...")
        applications_file = os.path.join(frontend_data_dir, "applications.json")
        with open(applications_file, "r") as f:
            applications_data = json.load(f)
        
        # Clear existing applications
        await db.applications.delete_many({})
        
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
        
        # Insert transformed applications
        result = await db.applications.insert_many(applications_to_insert)
        print(f"   ✅ Inserted {len(result.inserted_ids)} applications (transformed reviewerFeedback → reviewHistory)")
        
        # 4. Load Projects (exactly as-is)
        print("🚀 Loading projects...")
        projects_file = os.path.join(frontend_data_dir, "projects.json")
        with open(projects_file, "r") as f:
            projects_data = json.load(f)
        
        # Clear existing projects
        await db.projects.delete_many({})
        
        # Insert exactly as-is
        result = await db.projects.insert_many(projects_data["projects"])
        print(f"   ✅ Inserted {len(result.inserted_ids)} projects")
        
        # 5. Create basic indexes for performance
        print("🔍 Creating database indexes...")
        await db.users.create_index("email", unique=True)
        await db.applications.create_index("email")
        await db.applications.create_index("grantId")
        await db.applications.create_index("status")
        await db.grant_calls.create_index("id")
        await db.projects.create_index("applicationId")
        print("   ✅ Indexes created")
        
        print()
        print("🎉 Frontend data loaded successfully!")
        print("=" * 50)
        print(f"Users: {len(users_data['users'])}")
        print(f"Grant Calls: {len(grant_calls_data['grantCalls'])}")
        print(f"Applications: {len(applications_data['applications'])}")
        print(f"Projects: {len(projects_data['projects'])}")
        print("=" * 50)
        print()
        print("Demo credentials:")
        for user in users_data["users"]:
            print(f"• {user['email']} / {user['password']} ({user['role']})")
        
        return True  # Indicate success
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

def main():
    """Main function to run the async loader with proper error handling."""
    try:
        print("🔄 Starting frontend data loader...")
        success = asyncio.run(load_frontend_data())
        
        if success:
            print("✅ Data loading completed successfully!")
            sys.exit(0)  # Explicit success exit
        else:
            print("❌ Data loading failed!")
            sys.exit(1)  # Explicit failure exit
            
    except KeyboardInterrupt:
        print("\n⚠️  Data loading interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
