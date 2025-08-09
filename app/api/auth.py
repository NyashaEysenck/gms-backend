from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..database import get_database
from ..schemas.user import Token, UserLogin, UserResponse, TokenWithUser
from ..services.user_service import authenticate_user, get_user_by_email
from ..utils.security import create_access_token
from ..config import settings
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenWithUser)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = await get_database()
    
    # Authenticate user without role requirement
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at.isoformat()
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user_response
    }

@router.post("/login-custom", response_model=Token)
async def login_custom(user_login: UserLogin):
    db = await get_database()
    
    user = await authenticate_user(db, user_login.email, user_login.password, user_login.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or role"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        created_at=current_user.created_at.isoformat()
    )
