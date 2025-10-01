"""
Centralized error handling for the RNA Analysis application
"""
from typing import Optional, Dict, Any, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import traceback
from .logger import log_error, api_logger, system_logger


class RNAAnalysisException(Exception):
    """Base exception for RNA Analysis application"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RNAAnalysisException):
    """Exception for validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class ClassificationError(RNAAnalysisException):
    """Exception for classification errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class VectorDBError(RNAAnalysisException):
    """Exception for vector database errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class ModelNotLoadedError(RNAAnalysisException):
    """Exception when ML model is not loaded"""
    def __init__(self, message: str = "Model not loaded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE, details)


class SequenceTooLongError(ValidationError):
    """Exception for sequences exceeding maximum length"""
    def __init__(self, length: int, max_length: int):
        super().__init__(
            f"Sequence length {length} exceeds maximum {max_length}",
            {"length": length, "max_length": max_length}
        )


class InvalidSequenceError(ValidationError):
    """Exception for invalid RNA sequences"""
    def __init__(self, sequence: str, errors: list):
        super().__init__(
            "Invalid RNA sequence",
            {"sequence": sequence[:100], "errors": errors}
        )


def create_error_response(
    error: Exception,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    if isinstance(error, RNAAnalysisException):
        return {
            "success": False,
            "error": {
                "message": error.message,
                "type": error.__class__.__name__,
                "details": error.details,
                "request_id": request_id
            },
            "status_code": error.status_code
        }
    elif isinstance(error, HTTPException):
        return {
            "success": False,
            "error": {
                "message": error.detail,
                "type": "HTTPException",
                "status_code": error.status_code,
                "request_id": request_id
            },
            "status_code": error.status_code
        }
    else:
        return {
            "success": False,
            "error": {
                "message": str(error),
                "type": error.__class__.__name__,
                "request_id": request_id
            },
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for FastAPI"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log the error
    log_error(
        api_logger,
        f"Unhandled exception in {request.method} {request.url.path}",
        exception=exc,
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )
    
    # Create error response
    error_response = create_error_response(exc, request_id)
    
    return JSONResponse(
        status_code=error_response["status_code"],
        content=error_response
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP exception handler for FastAPI"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log the error
    api_logger.warning(
        f"HTTP exception in {request.method} {request.url.path}: {exc.detail}",
        extra={
            'extra_data': {
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': exc.status_code
            }
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": request_id
            }
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Validation exception handler"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log the validation error
    api_logger.warning(
        f"Validation error in {request.method} {request.url.path}: {exc.message}",
        extra={
            'extra_data': {
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'details': exc.details
            }
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "type": "ValidationError",
                "details": exc.details,
                "request_id": request_id
            }
        }
    )


class ErrorHandler:
    """Error handler for Gradio application"""
    
    @staticmethod
    def handle_api_error(error: Union[Exception, Dict[str, Any]]) -> Dict[str, Any]:
        """Handle API errors in Gradio"""
        if isinstance(error, dict):
            return error
        
        if isinstance(error, RNAAnalysisException):
            return {
                "success": False,
                "error": error.message,
                "details": error.details
            }
        
        return {
            "success": False,
            "error": str(error),
            "details": {}
        }
    
    @staticmethod
    def safe_api_call(func, *args, **kwargs) -> Dict[str, Any]:
        """Safely call API functions with error handling"""
        try:
            result = func(*args, **kwargs)
            if not isinstance(result, dict):
                result = {"data": result}
            if "success" not in result:
                result["success"] = True
            return result
        except Exception as e:
            log_error(
                system_logger,
                f"Error in {func.__name__}",
                exception=e,
                args=str(args)[:200],
                kwargs=str(kwargs)[:200]
            )
            return ErrorHandler.handle_api_error(e)