from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
import base64
from datetime import datetime
from bson import ObjectId

from ...utils.dependencies import get_current_active_user, get_database
from ...services.application_service import get_application_by_id

router = APIRouter()

@router.get("/{application_id}/document/{filename}")
async def download_application_document(
    application_id: str,
    filename: str,
    current_user = Depends(get_current_active_user)
):
    """Download application document stored as base64 in MongoDB"""
    db = await get_database()
    application = await get_application_by_id(db, application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check permissions - only grants managers, reviewers, and the applicant can download
    if (current_user.role not in ["Grants Manager", "Admin"] and 
        current_user.email != application.email):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify the filename matches the application's proposal file
    if application.proposal_file_name != filename:
        raise HTTPException(status_code=404, detail="Document not found for this application")
    
    # Check if file data exists in database
    if not application.proposal_file_data:
        raise HTTPException(status_code=404, detail="File data not found in database")
    
    try:
        # Decode base64 file data
        file_bytes = base64.b64decode(application.proposal_file_data)
        
        # Determine media type
        media_type = application.proposal_file_type or 'application/octet-stream'
        
        # Return the file as a response
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_bytes))
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding file data: {str(e)}")

@router.post("/{application_id}/award-letter/generate")
async def generate_award_letter(
    application_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Generate an award letter for an application.
    This creates a simple HTML-based letter, stores it base64-encoded on the application
    document (consistent with proposal storage), and marks the flag as generated.
    Only allowed when the application has reached signoff_approved.
    """
    db = await get_database()
    application = await get_application_by_id(db, application_id)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Only Grants Managers and Admins can trigger generation
    if current_user.role not in ["Grants Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Only grants managers can generate award letters")

    # Must be fully approved by sign-off
    if application.status != "signoff_approved":
        raise HTTPException(status_code=400, detail="Award letter can only be generated after sign-off approval")

    # If already generated, return current state (idempotent behavior)
    if getattr(application, "award_letter_generated", False) and getattr(application, "award_letter_file_data", None):
        return {"detail": "Award letter already generated"}

    # Pull details for the letter
    applicant_name = getattr(application, 'applicant_name', getattr(application, 'applicantName', None)) or getattr(application, 'email', 'Applicant')
    proposal_title = getattr(application, 'proposal_title', getattr(application, 'proposalTitle', 'Your Research Proposal'))
    email = getattr(application, 'email', '')

    # Award amount from signoff_workflow
    workflow = getattr(application, 'signoff_workflow', {}) or {}
    award_amount = None
    try:
        award_amount = workflow.get('award_amount') if isinstance(workflow, dict) else None
    except Exception:
        award_amount = None

    # Build a minimal HTML letter (keeps consistency without external PDF deps)
    generated_at = datetime.utcnow()
    pretty_date = generated_at.strftime('%B %d, %Y')
    amount_text = f"${award_amount:,.2f}" if isinstance(award_amount, (int, float)) else "Not specified"
    html_content = f"""
    <html>
      <head><meta charset='utf-8'><title>Award Letter</title></head>
      <body>
        <h2>Official Award Letter</h2>
        <p>Date: {pretty_date}</p>
        <p>To: {applicant_name} ({email})</p>
        <p>Subject: Award for "{proposal_title}"</p>
        <p>Congratulations! Your application has been approved following institutional sign-off.</p>
        <p><strong>Award Amount:</strong> {amount_text}</p>
        <p>This letter confirms your award. Please proceed to download this letter and follow up with contract submission as required.</p>
        <p>Sincerely,<br/>Grants Office</p>
      </body>
    </html>
    """.strip()

    file_bytes = html_content.encode('utf-8')
    file_b64 = base64.b64encode(file_bytes).decode('utf-8')
    filename = f"award_letter_{application_id}.html"
    file_type = "text/html"

    # Update application: set award letter fields and flag
    result = await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": {
            "award_letter_generated": True,
            "award_letter_generated_at": generated_at,
            "award_letter_file_name": filename,
            "award_letter_file_type": file_type,
            "award_letter_file_data": file_b64,
            "updated_at": generated_at
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to generate award letter")

    # Return a minimal response; frontend will refetch application details
    return {"detail": "Award letter generated"}

@router.get("/{application_id}/award-letter")
async def download_award_letter(
    application_id: str,
    current_user = Depends(get_current_active_user)
):
    """Download the generated award letter stored as base64 on the application document"""
    db = await get_database()
    application = await get_application_by_id(db, application_id)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Permission: applicant, Grants Manager, Admin
    if (getattr(current_user, 'role', None) not in ["Grants Manager", "Admin"] and
        getattr(current_user, 'email', None) != getattr(application, 'email', None)):
        raise HTTPException(status_code=403, detail="Access denied")

    # Ensure letter exists
    file_name = getattr(application, 'award_letter_file_name', None)
    file_type = getattr(application, 'award_letter_file_type', None) or 'application/octet-stream'
    file_data = getattr(application, 'award_letter_file_data', None)

    if not file_name or not file_data:
        raise HTTPException(status_code=404, detail="Award letter not found. Generate it first.")

    try:
        file_bytes = base64.b64decode(file_data)
        return Response(
            content=file_bytes,
            media_type=file_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_name}",
                "Content-Length": str(len(file_bytes))
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error decoding award letter: {str(e)}")
