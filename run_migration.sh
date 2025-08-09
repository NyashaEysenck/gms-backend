#!/bin/bash

# Data Migration Script for Grants Management System
# This script migrates JSON data from src/data to MongoDB

echo "Starting Grants Management System Data Migration..."
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Install required packages if not already installed
echo "Installing required Python packages..."
pip3 install motor passlib python-dotenv

# Set environment variables (you can modify these or use a .env file)
export MONGODB_URI=${MONGODB_URI:-"mongodb://localhost:27017"}
export DATABASE_NAME=${DATABASE_NAME:-"grants_management"}

echo "Using MongoDB URI: $MONGODB_URI"
echo "Using Database: $DATABASE_NAME"

# Check if MongoDB is running
echo "Checking MongoDB connection..."
python3 -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def check_connection():
    try:
        client = AsyncIOMotorClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
        await client.admin.command('ping')
        print('MongoDB connection successful!')
        client.close()
        return True
    except Exception as e:
        print(f'MongoDB connection failed: {e}')
        return False

if not asyncio.run(check_connection()):
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "Error: Cannot connect to MongoDB. Please ensure MongoDB is running."
    exit 1
fi

# Check if JSON data files exist
echo "Checking for JSON data files..."
if [ ! -f "../src/data/users.json" ]; then
    echo "Error: users.json not found in ../src/data/"
    exit 1
fi

if [ ! -f "../src/data/grantCalls.json" ]; then
    echo "Error: grantCalls.json not found in ../src/data/"
    exit 1
fi

if [ ! -f "../src/data/applications.json" ]; then
    echo "Error: applications.json not found in ../src/data/"
    exit 1
fi

if [ ! -f "../src/data/projects.json" ]; then
    echo "Error: projects.json not found in ../src/data/"
    exit 1
fi

echo "All JSON data files found!"

# Run the migration script
echo "Running data migration..."
python3 migrate_data.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Data migration completed successfully!"
    echo ""
    echo "You can now start your FastAPI server with:"
    echo "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
else
    echo "❌ Data migration failed. Please check the error messages above."
    exit 1
fi