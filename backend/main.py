"""
SR Automation Service - Main Entry Point

FastAPI application for querying ServiceNow tables.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import requests

from backend.config import load_config
from backend.utils.logger import setup_logger
from backend.utils.rate_limiter import create_rate_limiter
from backend.modules.models import QueryResponse


# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Determine environment
servicenow_environment = os.getenv("SERVICENOW_ENVIRONMENT", "dev").lower()

# Load configuration
sr_config_dir = f"configs/{servicenow_environment}"
sr_config = load_config(sr_config_dir)

# Set up logger
logger = setup_logger(sr_config)

# Set up rate limiter
rate_limit_config = sr_config.get("rate_limit", {})
rate_limiter = None
if rate_limit_config.get("enabled", False):
    rate_limiter = create_rate_limiter({"rate_limit": rate_limit_config})
    excluded_paths = rate_limit_config.get("excluded_paths", [])
    logger.info(f"Rate limiting enabled: {rate_limit_config.get('max_calls_per_day')} calls/day per IP")
else:
    logger.info("Rate limiting disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    logger.info(f"Starting {sr_config.get('app', {}).get('name', 'SR Automation Service')}")
    logger.info(f"Environment: {servicenow_environment}")
    yield
    logger.info("Shutting down")


# Create FastAPI app
app = FastAPI(
    title=sr_config.get("app", {}).get("name", "SR Automation Service"),
    version=sr_config.get("app", {}).get("version", "1.0.0"),
    description="Backend API service for querying ServiceNow tables",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": sr_config.get("app", {}).get("name", "SR Automation Service"),
        "version": sr_config.get("app", {}).get("version", "1.0.0"),
        "environment": servicenow_environment,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/query/{table_name}", response_model=QueryResponse)
async def query_table(
    request: Request,
    table_name: str,
    limit: int = 10
):
    """
    Query ServiceNow table to retrieve records.
    
    Args:
        request: FastAPI request object (for rate limiting)
        table_name: ServiceNow table name (e.g., "sc_request")
        limit: Maximum number of records to return (default: 10)
        
    Returns:
        QueryResponse with records from ServiceNow
    """
    # Check rate limit
    if rate_limiter:
        rate_limiter.check_rate_limit(request)
    
    logger.info(f"Query request for table: {table_name}, limit: {limit}")
    
    # Validate inputs
    if not table_name or len(table_name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Table name cannot be empty")
    
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    try:
        # Import and call ServiceNow module
        from backend.modules import servicenow
        
        servicenow_response = servicenow.query_table(
            sr_config=sr_config,
            table_name=table_name,
            limit=limit
        )
        
        # Extract records from ServiceNow response
        servicenow_records = servicenow_response.get("result", [])
        
        logger.info(f"Successfully retrieved {len(servicenow_records)} records from {table_name}")
        
        return QueryResponse(
            status="success",
            message=f"Successfully retrieved {len(servicenow_records)} records from {table_name}",
            table_name=table_name,
            count=len(servicenow_records),
            records=servicenow_records
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except requests.exceptions.RequestException as e:
        logger.error(f"ServiceNow API error: {e}")
        raise HTTPException(status_code=502, detail=f"ServiceNow API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal server error occurred",
            "error_code": "INTERNAL_ERROR"
        }
    )

