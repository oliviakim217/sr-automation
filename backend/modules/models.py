"""
Pydantic models for Service Request API request and response validation.

Simple models for request/response structures.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CreateSRRequest(BaseModel):
    """Request model for creating a Service Request."""
    
    caller_id: str = Field(...)
    short_description: str = Field(..., min_length=1, max_length=500)
    description: str = Field(...)
    assigned_to: Optional[str] = Field(None)


class CreateSRResponse(BaseModel):
    """Response model for Service Request creation."""
    
    status: str = Field(...)
    message: str = Field(...)
    request_id: Optional[str] = Field(None) # only return REQ ID e.g. REQ000001 


class QueryResponse(BaseModel):
    """Response model for querying ServiceNow records."""
    
    status: str = Field(...)
    message: str = Field(...)
    table_name: str = Field(...)
    count: int = Field(...)
    records: List[Dict[str, Any]] = Field(...)
    error_code: Optional[str] = Field(None)
    error_details: Optional[str] = Field(None)

