"""
Pydantic models for Service Request API request and response validation.

Simple models for request/response structures.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


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

