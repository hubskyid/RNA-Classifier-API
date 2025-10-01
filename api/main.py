from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .routes.classification import router as classification_router
from utils.config import config
from utils.logger import api_logger, log_api_request
from utils.error_handler import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    ValidationError
)
import time

# Ensure directories exist
config.ensure_directories()

# FastAPI
app = FastAPI(
    title="RNA Analysis API",
    description="API for RNA sequence analysis, classification, and vector search",
    version="1.0.0",
    debug=config.DEBUG,
    openapi_tags=[
        {
            "name": "RNA Analysis",
            "description": "Validation, classification, and vector search of RNA sequences"
        }
    ]
)

# CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response_time = time.time() - start_time
    
    log_api_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        response_time=response_time
    )
    
    return response

# Register router
app.include_router(classification_router)


@app.get("/", tags=["Root"])
async def root():
    """API"""
    return {
        "message": "RNA Analysis API",
        "description": "RNA sequence analysis, classification, and vector search",
        "version": "1.0.0",
        "endpoints": {
            "validation": "/api/v1/validate",
            "classification": "/api/v1/classify", 
            "vector_search": "/api/v1/search",
            "health_check": "/api/v1/health",
            "documentation": "/docs"
        }
    }


# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


if __name__ == "__main__":
    api_logger.info(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    api_logger.info(f"Environment: {config.ENVIRONMENT}")
    api_logger.info(f"Debug mode: {config.DEBUG}")
    
    # Preload models in background to avoid timeout during first request
    if config.ENVIRONMENT == "development":
        api_logger.info("Development mode: Using mock encoder for faster startup")
    
    uvicorn.run(
        "api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        log_level=config.API_LOG_LEVEL.lower(),
        workers=config.API_WORKERS if not config.API_RELOAD else 1
    )