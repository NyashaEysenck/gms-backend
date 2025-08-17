from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class ErrorCode(str, Enum):
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    UNAUTHORIZED = "UNAUTHORIZED"
    
    # Rate limiting
    RATE_LIMITED = "RATE_LIMITED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"
    
    # Server errors
    SERVER_ERROR = "SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Network/Connection errors
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"

class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[str] = None
    field: Optional[str] = None
    retry_after: Optional[int] = None  # seconds
    suggestions: Optional[list[str]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    timestamp: str
    request_id: Optional[str] = None

class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    code: str

class ValidationErrorResponse(BaseModel):
    error: ErrorDetail
    validation_errors: list[ValidationErrorDetail]
    timestamp: str
    request_id: Optional[str] = None

# Error message mappings for user-friendly display
ERROR_MESSAGES = {
    ErrorCode.INVALID_CREDENTIALS: {
        "message": "Invalid email or password",
        "details": "Please check your credentials and try again",
        "suggestions": ["Verify your email address", "Check if Caps Lock is on", "Try resetting your password"]
    },
    ErrorCode.ACCOUNT_LOCKED: {
        "message": "Account temporarily locked",
        "details": "Too many failed login attempts. Please try again later",
        "suggestions": ["Wait before trying again", "Contact support if you need immediate access"]
    },
    ErrorCode.ACCOUNT_DISABLED: {
        "message": "Account disabled",
        "details": "Your account has been disabled. Please contact support",
        "suggestions": ["Contact system administrator", "Check your email for account status updates"]
    },
    ErrorCode.RATE_LIMITED: {
        "message": "Too many requests",
        "details": "Please wait before making another request",
        "suggestions": ["Wait a moment before trying again", "Check your internet connection"]
    },
    ErrorCode.SERVER_ERROR: {
        "message": "Server error occurred",
        "details": "An unexpected error occurred. Please try again",
        "suggestions": ["Try again in a few moments", "Contact support if the problem persists"]
    },
    ErrorCode.NETWORK_ERROR: {
        "message": "Network connection error",
        "details": "Unable to connect to the server",
        "suggestions": ["Check your internet connection", "Try refreshing the page"]
    },
    ErrorCode.TOKEN_EXPIRED: {
        "message": "Session expired",
        "details": "Your session has expired. Please log in again",
        "suggestions": ["Log in again", "Enable 'Remember me' for longer sessions"]
    }
}

def create_error_response(
    error_code: ErrorCode,
    custom_message: Optional[str] = None,
    custom_details: Optional[str] = None,
    field: Optional[str] = None,
    retry_after: Optional[int] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    from datetime import datetime
    
    error_info = ERROR_MESSAGES.get(error_code, {
        "message": "An error occurred",
        "details": "Please try again",
        "suggestions": ["Try again later"]
    })
    
    error_detail = ErrorDetail(
        code=error_code,
        message=custom_message or error_info["message"],
        details=custom_details or error_info["details"],
        field=field,
        retry_after=retry_after,
        suggestions=error_info.get("suggestions")
    )
    
    return ErrorResponse(
        error=error_detail,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id
    )
