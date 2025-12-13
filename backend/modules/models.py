"""
Pydantic models for Service Request API request and response validation.

Simple models for request/response structures.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CreateSRRequest(BaseModel):
    """Request model for creating a Service Request."""
    
    short_description: str = Field(..., min_length=1, max_length=500)
    caller_id: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    subcategory: Optional[str] = Field(None)
    description: Optional[str] = Field(None)


class CreateSRResponse(BaseModel):
    """Response model for Service Request creation."""
    
    status: str = Field(..., description="Response status: 'success' or 'error'")
    message: str = Field(..., description="Human-readable message describing the result")
    sr_number: Optional[str] = Field(None, description="Service Request number")
    sys_id: Optional[str] = Field(None, description="ServiceNow sys_id of created record")


class QueryResponse(BaseModel):
    """Response model for querying ServiceNow records."""
    
    # Required fields
    status: str = Field( 
        ...,
        description="Response status: 'success' or 'error'"
    )
    message: str = Field(
        ...,
        description="Human-readable message describing the result"
    )
    table_name: str = Field(
        ...,
        description="ServiceNow table name that was queried"
    )
    count: int = Field(
        ...,
        description="Number of records returned"
    )
    records: List[Dict[str, Any]] = Field(
        ...,
        description="List of records from ServiceNow"
    )
    
    # Optional error fields (only present when status is 'error')
    error_code: Optional[str] = Field(
        None,
        description="Error code (only present on error)"
    )
    error_details: Optional[str] = Field(
        None,
        description="Additional error details (only present on error)"
    )

