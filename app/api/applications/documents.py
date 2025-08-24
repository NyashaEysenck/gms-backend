from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
import base64

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
