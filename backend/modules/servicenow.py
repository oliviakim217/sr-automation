"""
ServiceNow API integration module.

Implements ServiceNow Table API based on official documentation:
https://www.servicenow.com/docs/bundle/xanadu-api-reference/page/integrate/inbound-rest/concept/c_TableAPI.html

Simple module to query ServiceNow tables using the Table API.
"""

import os
import requests
from typing import Dict, Any, Optional, Tuple
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError

from backend.utils.logger import get_logger

logger = get_logger("sr_automation")


def _get_credentials() -> Tuple[str, str]:
    """Get ServiceNow credentials from environment variables."""
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")
    
    if not username or not password:
        raise ValueError("SERVICENOW_USERNAME and SERVICENOW_PASSWORD must be set")
    
    return username, password


def _get_instance_url(config: Dict[str, Any]) -> str:
    """Get ServiceNow instance URL from config or environment variable."""
    instance_url = config.get("servicenow", {}).get("instance_url", "")
    
    if not instance_url:
        instance_url = os.getenv("SERVICENOW_INSTANCE_URL", "")
    
    if not instance_url:
        raise ValueError("SERVICENOW_INSTANCE_URL must be set")
    
    # Remove trailing slash and ensure https://
    instance_url = instance_url.rstrip("/")
    if not instance_url.startswith("http"):
        instance_url = f"https://{instance_url}"
    
    return instance_url


def query_table(
    config: Dict[str, Any],
    table_name: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Query ServiceNow table to retrieve records.
    
    Args:
        config: Configuration dictionary
        table_name: ServiceNow table name (e.g., "sc_request")
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with ServiceNow API response (records in 'result' key)
    """
    logger.info(f"Querying ServiceNow table: {table_name}")
    
    instance_url = _get_instance_url(config)
    username, password = _get_credentials()
    
    # Get API path from config (defaults to /api/now/table per ServiceNow Table API)
    api_path = config.get("servicenow", {}).get("api_path", "/api/now/table")
    
    # Build API URL according to ServiceNow Table API: {instance}/api/now/table/{table_name}
    api_url = f"{instance_url}{api_path}/{table_name}"
    
    # Get default query params from config and override limit with function parameter
    default_params = config.get("servicenow", {}).get("query_params", {})
    params = {**default_params}  # Start with defaults from config
    params["sysparm_limit"] = limit  # Override with function parameter
    
    # Get headers from config
    # For GET requests, only Accept header is required per ServiceNow Table API
    default_headers = config.get("servicenow", {}).get("headers", {
        "Accept": "application/json"
    })
    # Ensure Accept header is set (required for ServiceNow Table API)
    if "Accept" not in default_headers:
        default_headers["Accept"] = "application/json"
    
    try:
        response = requests.get(
            api_url,
            params=params,
            auth=HTTPBasicAuth(username, password),
            headers=default_headers,
            timeout=30
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        record_count = len(response_data.get("result", []))
        logger.info(f"Retrieved {record_count} records from {table_name}")
        
        return response_data
        
    except Timeout:
        logger.error(f"Timeout querying {table_name}")
        raise RequestException("ServiceNow API request timed out")
    except RequestsConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise RequestException(f"Failed to connect to ServiceNow: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        # Parse ServiceNow error response if available
        error_message = str(e)
        try:
            error_response = response.json()
            if "error" in error_response:
                error_detail = error_response["error"]
                error_message = error_detail.get("message", error_detail.get("detail", str(e)))
        except:
            pass  # Use default error message if parsing fails
        
        if response.status_code == 401:
            raise RequestException("ServiceNow authentication failed. Please check credentials.")
        elif response.status_code == 403:
            raise RequestException(f"Access denied to table '{table_name}'. Check user permissions.")
        elif response.status_code == 404:
            raise RequestException(f"Table '{table_name}' not found or access denied.")
        else:
            raise RequestException(f"ServiceNow API error ({response.status_code}): {error_message}")
    except Exception as e:
        logger.error(f"Error querying {table_name}: {e}")
        raise RequestException(f"ServiceNow API request failed: {e}")

