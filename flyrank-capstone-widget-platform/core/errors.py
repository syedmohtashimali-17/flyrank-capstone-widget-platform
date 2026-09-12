from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class APIError(HTTPException):
    """Base API error class."""
    
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[Any]] = None
    ):
        self.code = code
        self.details = details or []
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": self.details
                }
            }
        )


class ValidationError(APIError):
    """Validation error."""
    
    def __init__(self, message: str = "Invalid request payload.", details: Optional[List[Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details
        )


class NotFoundError(APIError):
    """Not found error."""
    
    def __init__(self, message: str = "Resource not found."):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message
        )


class UnauthorizedError(APIError):
    """Unauthorized error."""
    
    def __init__(self, message: str = "Authentication required."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message
        )


class ForbiddenError(APIError):
    """Forbidden error."""
    
    def __init__(self, message: str = "Access forbidden."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message
        )


class PayloadTooLargeError(APIError):
    """Payload too large error."""
    
    def __init__(self, message: str = "Request body exceeds the maximum allowed size."):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="PAYLOAD_TOO_LARGE",
            message=message
        )


class TooManyRequestsError(APIError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="TOO_MANY_REQUESTS",
            message=message
        )