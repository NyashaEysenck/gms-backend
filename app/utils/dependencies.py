from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..utils.security import verify_token
from ..services.user_service import get_user_by_email
from ..db_config import get_database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = verify_token(token, credentials_exception)
    db = await get_database()
    user = await get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    print(f"DEBUG AUTH: get_current_active_user called for {current_user.email} (role: {current_user.role}, status: {current_user.status})")
    if current_user.status != "active":
        print(f"DEBUG AUTH: User {current_user.email} is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    print(f"DEBUG AUTH: User {current_user.email} is active")
    return current_user

def require_role(required_role: str):
    def role_checker(current_user = Depends(get_current_active_user)):
        if current_user.role != required_role and current_user.role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker