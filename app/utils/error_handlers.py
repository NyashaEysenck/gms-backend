from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
import uuid
import logging
from typing import Union

from ..schemas.error import (
    ErrorCode, 
    ErrorResponse, 
    ValidationErrorResponse, 
    ValidationErrorDetail,
    create_error_response
)

logger = logging.getLogger(__name__)

class AuthenticationError(HTTPException):
    """Custom authentication error with detailed error codes"""
    def __init__(
        self, 
        error_code: ErrorCode, 
        message: str = None, 
        details: str = None,
        retry_after: int = None
    ):
        self.error_code = error_code
        self.custom_message = message
        self.custom_details = details
        self.retry_after = retry_after
        
        # Map error codes to HTTP status codes
        status_code_map = {
            ErrorCode.INVALID_CREDENTIALS: 401,
            ErrorCode.ACCOUNT_LOCKED: 423,  # Locked
            ErrorCode.ACCOUNT_DISABLED: 403,
            ErrorCode.TOKEN_EXPIRED: 401,
            ErrorCode.TOKEN_INVALID: 401,
            ErrorCode.UNAUTHORIZED: 401,
            ErrorCode.RATE_LIMITED: 429,
            ErrorCode.TOO_MANY_ATTEMPTS: 429,
        }
        
        status_code = status_code_map.get(error_code, 400)
        super().__init__(status_code=status_code, detail=message or error_code.value)

async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors with detailed responses"""
    request_id = str(uuid.uuid4())
    
    # Log the error for debugging
    logger.warning(f"Authentication error: {exc.error_code} - {exc.custom_message} (Request ID: {request_id})")
    
    error_response = create_error_response(
        error_code=exc.error_code,
        custom_message=exc.custom_message,
        custom_details=exc.custom_details,
        retry_after=exc.retry_after,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id}
    )

async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]):
    """Handle general HTTP exceptions"""
    request_id = str(uuid.uuid4())
    
    # Map HTTP status codes to error codes
    status_to_error_code = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.UNAUTHORIZED,
        404: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
        500: ErrorCode.SERVER_ERROR,
        502: ErrorCode.SERVICE_UNAVAILABLE,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    
    error_code = status_to_error_code.get(exc.status_code, ErrorCode.SERVER_ERROR)
    
    # Log the error
    logger.error(f"HTTP error {exc.status_code}: {exc.detail} (Request ID: {request_id})")
    
    error_response = create_error_response(
        error_code=error_code,
        custom_message=str(exc.detail) if exc.detail else None,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with field-specific details"""
    request_id = str(uuid.uuid4())
    
    # Extract validation errors
    validation_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        validation_errors.append(ValidationErrorDetail(
            field=field,
            message=error["msg"],
            code=error["type"]
        ))
    
    # Log validation errors
    logger.warning(f"Validation errors: {len(validation_errors)} errors (Request ID: {request_id})")
    
    error_response = ValidationErrorResponse(
        error=create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            custom_message="Validation failed",
            custom_details="Please check the provided data",
            request_id=request_id
        ).error,
        validation_errors=validation_errors,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = str(uuid.uuid4())
    
    # Log the unexpected error
    logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)} (Request ID: {request_id})", exc_info=True)
    
    error_response = create_error_response(
        error_code=ErrorCode.SERVER_ERROR,
        custom_message="An unexpected error occurred",
        custom_details="Please try again later",
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict(),
        headers={"X-Request-ID": request_id}
    )

# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter for login attempts"""
    def __init__(self):
        self.attempts = {}  # {email: {"count": int, "last_attempt": datetime, "locked_until": datetime}}
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes in seconds
        self.window_duration = 300   # 5 minutes in seconds
    
    def is_rate_limited(self, email: str) -> tuple[bool, int]:
        """Check if email is rate limited. Returns (is_limited, retry_after_seconds)"""
        now = datetime.utcnow()
        
        if email not in self.attempts:
            return False, 0
        
        attempt_data = self.attempts[email]
        
        # Check if still locked out
        if "locked_until" in attempt_data and now < attempt_data["locked_until"]:
            retry_after = int((attempt_data["locked_until"] - now).total_seconds())
            return True, retry_after
        
        # Reset if window has passed
        if "last_attempt" in attempt_data:
            time_since_last = (now - attempt_data["last_attempt"]).total_seconds()
            if time_since_last > self.window_duration:
                self.attempts[email] = {"count": 0, "last_attempt": now}
                return False, 0
        
        return False, 0
    
    def record_attempt(self, email: str, success: bool):
        """Record a login attempt"""
        now = datetime.utcnow()
        
        if email not in self.attempts:
            self.attempts[email] = {"count": 0, "last_attempt": now}
        
        if success:
            # Reset on successful login
            self.attempts[email] = {"count": 0, "last_attempt": now}
        else:
            # Increment failed attempts
            self.attempts[email]["count"] += 1
            self.attempts[email]["last_attempt"] = now
            
            # Lock account if too many attempts
            if self.attempts[email]["count"] >= self.max_attempts:
                from datetime import timedelta
                self.attempts[email]["locked_until"] = now + timedelta(seconds=self.lockout_duration)

# Global rate limiter instance
rate_limiter = RateLimiter()
