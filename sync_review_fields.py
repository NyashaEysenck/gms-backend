#!/usr/bin/env python3
"""
Simple script to sync reviewComments with latest reviewHistory entry
Run this once to fix existing data inconsistencies
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def sync_review_fields():
    """Sync reviewComments field with latest reviewHistory entry for all applications"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.grants_management
    
    print("🔄 Syncing reviewComments with reviewHistory...")
    
    # Find applications with reviewHistory
    applications = await db.applications.find({
        "reviewHistory": {"$exists": True, "$ne": []}
    }).to_list(None)
    
    updated_count = 0
    
    for app in applications:
        review_history = app.get("reviewHistory", [])
        if review_history:
            # Get the latest review comment
            latest_comment = review_history[-1].get("comments", "")
            current_comment = app.get("reviewComments", "")
            
            # Update if different
            if latest_comment != current_comment:
                await db.applications.update_one(
                    {"_id": app["_id"]},
                    {"$set": {"reviewComments": latest_comment}}
                )
                updated_count += 1
                print(f"   ✅ Updated application {app['_id']}")
    
    print(f"🎉 Sync complete! Updated {updated_count} applications")
    client.close()

if __name__ == "__main__":
    asyncio.run(sync_review_fields())
