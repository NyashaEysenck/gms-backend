from fastapi import APIRouter, Depends, HTTPException
from ..utils.dependencies import get_current_active_user
from ..models.user import User
from ..database.loader import load_data_from_json

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

@router.post("/reset-database", status_code=200)
async def reset_database(current_user: User = Depends(get_current_active_user)):
    try:
        if current_user.role != "Admin":
            raise HTTPException(
                status_code=403, 
                detail={"message": "Only admins can perform this action"}
            )
        
        result = await load_data_from_json()
        if "error" in result:
            raise HTTPException(
                status_code=500, 
                detail={"message": f"Failed to reset database: {result['error']}"}
            )
        
        return {"message": "Database reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={"message": f"An unexpected error occurred: {str(e)}"}
        )
