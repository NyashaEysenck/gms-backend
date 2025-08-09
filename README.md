# Grants Management System - Backend Migration

This directory contains the FastAPI backend and data migration scripts for the Grants Management System.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Copy `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=grants_management
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### 3. Start MongoDB
Make sure MongoDB is running:
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or using local MongoDB installation
mongod
```

### 4. Migrate Sample Data
Run the migration script to populate MongoDB with your existing JSON data:
```bash
chmod +x run_migration.sh
./run_migration.sh
```

Or run the Python script directly:
```bash
python migrate_data.py
```

### 5. Start the FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once the server is running, you can access:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Sample Data

The migration script will populate MongoDB with:
- **3 Users** (Researcher, Grants Manager, Admin)
- **5 Grant Calls** (Various research and innovation opportunities)
- **3 Applications** (Different statuses: approved, under review, needs revision)
- **2 Projects** (One completed, one on hold)

### Default User Credentials
After migration, you can login with:

**Researcher:**
- Email: researcher@grants.edu
- Password: research123
- Role: Researcher

**Grants Manager:**
- Email: manager@grants.edu
- Password: manager123
- Role: Grants Manager

**Admin:**
- Email: admin@grants.edu
- Password: admin123
- Role: Admin

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/login-custom` - Custom login format
- `GET /auth/me` - Get current user info

### Users Management
- `GET /users/` - List all users (Admin only)
- `POST /users/` - Create new user (Admin only)
- `PUT /users/{id}` - Update user (Admin only)
- `DELETE /users/{id}` - Delete user (Admin only)

### Grant Calls
- `GET /grant-calls/` - List grant calls
- `POST /grant-calls/` - Create grant call (Grants Manager)
- `PUT /grant-calls/{id}` - Update grant call (Grants Manager)
- `PATCH /grant-calls/{id}/toggle-status` - Toggle open/closed

### Applications
- `GET /applications/` - List applications (filtered by user role)
- `POST /applications/` - Submit application
- `PUT /applications/{id}` - Update application
- `POST /applications/{id}/reviews` - Submit review

### Projects
- `GET /projects/` - List projects (filtered by user role)
- `POST /projects/` - Create project (Grants Manager)
- `POST /projects/{id}/milestones` - Add milestone
- `POST /projects/{id}/requisitions` - Submit requisition
- `POST /projects/{id}/partners` - Add partner

### Documents
- `POST /documents/upload` - Upload document
- `GET /documents/` - List documents
- `GET /documents/stats` - Get document statistics

## Database Schema

The system uses the following MongoDB collections:
- `users` - User accounts and authentication
- `grant_calls` - Available funding opportunities
- `applications` - Grant applications and reviews
- `projects` - Active projects with milestones
- `documents` - Document management with versioning

## Security Features

- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- Protected API endpoints
- CORS configuration

## Development

To run in development mode:
```bash
uvicorn app.main:app --reload
```

The server will automatically reload when you make changes to the code.