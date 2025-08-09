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
    print(f"📍 MongoDB URI: {settings.mongodb_uri}")
    print(f"📊 Database: {settings.database_name}")
    print()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    # Frontend data directory
    frontend_data_dir = "../src/data"
    
    try:
        # 1. Load Users (with password hashing)
        print("👥 Loading users...")
        with open(f"{frontend_data_dir}/users.json", "r") as f:
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
        with open(f"{frontend_data_dir}/grantCalls.json", "r") as f:
            grant_calls_data = json.load(f)
        
        # Clear existing grant calls
        await db.grant_calls.delete_many({})
        
        # Insert exactly as-is
        result = await db.grant_calls.insert_many(grant_calls_data["grantCalls"])
        print(f"   ✅ Inserted {len(result.inserted_ids)} grant calls")
        
        # 3. Load Applications (exactly as-is)
        print("📝 Loading applications...")
        with open(f"{frontend_data_dir}/applications.json", "r") as f:
            applications_data = json.load(f)
        
        # Clear existing applications
        await db.applications.delete_many({})
        
        # Insert exactly as-is
        result = await db.applications.insert_many(applications_data["applications"])
        print(f"   ✅ Inserted {len(result.inserted_ids)} applications")
        
        # 4. Load Projects (exactly as-is)
        print("🚀 Loading projects...")
        with open(f"{frontend_data_dir}/projects.json", "r") as f:
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
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(load_frontend_data())
