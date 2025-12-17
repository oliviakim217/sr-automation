"""
SR Automation Service - Main Entry Point

FastAPI application for querying ServiceNow tables.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import requests

from backend.constants import API_LIMIT_MAX, API_LIMIT_MIN
from backend.config import load_config
from backend.utils.logger import setup_logger
from backend.utils.rate_limiter import create_rate_limiter
from backend.modules.models import (
    TableQueryResponse,
    SRCreationInput,
    SRCreationResponse,
)


# Load environment variables
env_file_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file_path)

# Determine environment
env_servicenow_environment = os.getenv("SERVICENOW_ENVIRONMENT", "dev").lower()

# Load configuration (resolve path relative to main.py file location)
cfg_config_dir = Path(__file__).parent.parent / "configs" / env_servicenow_environment
cfg_app_config = load_config(str(cfg_config_dir))

# Set up logger
logger = setup_logger(cfg_app_config)

# Set up rate limiter
cfg_rate_limit_config = cfg_app_config.get("rate_limit", {})
rate_limiter = None
if cfg_rate_limit_config.get("enabled", False):
    rate_limiter = create_rate_limiter(cfg_app_config)
    logger.info(
        f"BEGIN:rate_limit enabled max_calls_per_day={cfg_rate_limit_config.get('max_calls_per_day')}"
    )
else:
    logger.info("BEGIN:rate_limit disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    logger.info(f"BEGIN:startup service={cfg_app_config.get('app', {}).get('name', 'SR Automation Service')}")
    logger.info(f"BEGIN:startup env={env_servicenow_environment}")
    yield
    logger.info("END:startup")


# Create FastAPI app
app = FastAPI(
    title=cfg_app_config.get("app", {}).get("name", "SR Automation Service"),
    version=cfg_app_config.get("app", {}).get("version", "1.0.0"),
    description="Backend API service for querying ServiceNow tables",
    lifespan=lifespan
)


@app.get("/")
async def api_root():
    """Root endpoint - API information."""
    return {
        "service": cfg_app_config.get("app", {}).get("name", "SR Automation Service"),
        "version": cfg_app_config.get("app", {}).get("version", "1.0.0"),
        "environment": env_servicenow_environment,
        "status": "running"
    }


@app.get("/health")
async def api_health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/query/{table_name}", response_model=TableQueryResponse)
async def api_get_table_records(
    request: Request,
    table_name: str,
    limit: int = 10
):
    """Query ServiceNow table to retrieve records."""
    # Check rate limit
    if rate_limiter:
        rate_limiter.check_rate_limit(request)
    
    logger.info(f"BEGIN:query_table table_name={table_name} limit={limit}")
    
    # Validate inputs
    if not table_name or len(table_name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Table name cannot be empty")
    
    if limit < API_LIMIT_MIN or limit > API_LIMIT_MAX:
        raise HTTPException(
            status_code=400,
            detail=f"Limit must be between {API_LIMIT_MIN} and {API_LIMIT_MAX}",
        )
    
    try:
        # Import and call ServiceNow module
        from backend.modules import servicenow
        
        servicenow_response = servicenow.fetch_table_records(
            cfg_app_config=cfg_app_config,
            table_name=table_name,
            limit=limit
        )
        
        # Extract records from ServiceNow response
        table_records = servicenow_response.get("result", [])
        
        logger.info(f"END:query_table table_name={table_name} count={len(table_records)}")
        
        return TableQueryResponse(
            status="success",
            message=f"Successfully retrieved {len(table_records)} records from {table_name}",
            table_name=table_name,
            count=len(table_records),
            records=table_records
        )
        
    except ValueError as e:
        logger.error(f"ERROR:query_table validation_error={e}")
        raise HTTPException(status_code=400, detail=str(e))
    except requests.exceptions.RequestException as e:
        logger.error(f"ERROR:query_table servicenow_error={e}")
        raise HTTPException(status_code=502, detail=f"ServiceNow API error: {str(e)}")
    except Exception as e:
        logger.error(f"ERROR:query_table unexpected_error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@app.post("/api/sr/create", response_model=SRCreationResponse)
async def api_create_service_request(request: Request, sr_request: SRCreationInput):
    """Create a Service Request in ServiceNow."""
    if rate_limiter:
        rate_limiter.check_rate_limit(request)
    
    logger.info(f"BEGIN:create_service_request short_description={sr_request.short_description[:50]}")
    
    try:
        from backend.modules import servicenow
        
        sr_request_payload = sr_request.model_dump(exclude_none=True)
        
        if not sr_request_payload.get("assigned_to"):
            sr_request_payload["assigned_to"] = sr_request.caller_id
        
        sr_creation_result = servicenow.create_sr(
            cfg_app_config=cfg_app_config,
            sr_request_payload=sr_request_payload
        )
        
        logger.info(f"Created SR: {sr_creation_result.get('request_id')}")
        
        return SRCreationResponse(
            status="success",
            message="Service Request created successfully",
            request_id=sr_creation_result.get("request_id")
        )
        
    except ValueError as e:
        logger.error(f"ERROR:create_service_request validation_error={e}")
        raise HTTPException(status_code=400, detail=str(e))
    except requests.exceptions.RequestException as e:
        logger.error(f"ERROR:create_service_request servicenow_error={e}")
        raise HTTPException(status_code=502, detail=f"ServiceNow API error: {str(e)}")
    except Exception as e:
        logger.error(f"ERROR:create_service_request unexpected_error={e}", exc_info=True)
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

