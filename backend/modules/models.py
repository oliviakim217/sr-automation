"""
Pydantic models for Service Request API request and response validation.

Simple models for request/response structures.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SRCreationInput(BaseModel):
    """Request model for creating a Service Request."""
    
    caller_id: str = Field(...)
    short_description: str = Field(..., min_length=1, max_length=500)
    description: str = Field(...)
    assigned_to: Optional[str] = Field(None)


class SRCreationResponse(BaseModel):
    """Response model for Service Request creation."""
    
    status: str = Field(...)
    message: str = Field(...)
    request_id: Optional[str] = Field(None) 
    sys_id: Optional[str] = Field(None)
    sys_created_on: Optional[str] = Field(None)
    sys_updated_on: Optional[str] = Field(None)
    opened_at: Optional[str] = Field(None)
    state: Optional[str] = Field(None)
    approval: Optional[str] = Field(None)
    request_state: Optional[str] = Field(None)
    stage: Optional[str] = Field(None)


class TableQueryResponse(BaseModel):
    """Response model for querying ServiceNow table records."""
    
    status: str = Field(...)
    message: str = Field(...)
    table_name: str = Field(...)
    count: int = Field(...)
    records: List[Dict[str, Any]] = Field(...)
    error_code: Optional[str] = Field(None)
    error_details: Optional[str] = Field(None)

