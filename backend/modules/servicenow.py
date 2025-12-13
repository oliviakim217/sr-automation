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


def _get_instance_url(sr_config: Dict[str, Any]) -> str:
    """Get ServiceNow instance URL from config or environment variable."""
    servicenow_instance_url = sr_config.get("servicenow", {}).get("instance_url", "")
    
    if not servicenow_instance_url:
        servicenow_instance_url = os.getenv("SERVICENOW_INSTANCE_URL", "")
    
    if not servicenow_instance_url:
        raise ValueError("SERVICENOW_INSTANCE_URL must be set")
    
    # Remove trailing slash and ensure https://
    servicenow_instance_url = servicenow_instance_url.rstrip("/")
    if not servicenow_instance_url.startswith("http"):
        servicenow_instance_url = f"https://{servicenow_instance_url}"
    
    return servicenow_instance_url


def fetch_table_records(
    sr_config: Dict[str, Any],
    table_name: str,
    limit: int = 10
) -> Dict[str, Any]:
    """Query ServiceNow table to retrieve records."""
    logger.info(f"Querying ServiceNow table: {table_name}")
    
    servicenow_instance_url = _get_instance_url(sr_config)
    servicenow_username, servicenow_password = _get_credentials()
    
    # Get API path from config (defaults to /api/now/table per ServiceNow Table API)
    servicenow_api_path = sr_config.get("servicenow", {}).get("api_path", "/api/now/table")
    
    servicenow_api_url = f"{servicenow_instance_url}{servicenow_api_path}/{table_name}"
    
    servicenow_query_params_default = sr_config.get("servicenow", {}).get("query_params", {})
    servicenow_query_params = {**servicenow_query_params_default}  # Start with defaults from config
    servicenow_query_params["sysparm_limit"] = limit  # Override with function parameter
    
    servicenow_api_headers = sr_config.get("servicenow", {}).get("headers", {
        "Accept": "application/json"
    })
    # Ensure Accept header is set (required for ServiceNow Table API)
    if "Accept" not in servicenow_api_headers:
        servicenow_api_headers["Accept"] = "application/json"
    
    try:
        servicenow_api_response = requests.get(
            servicenow_api_url,
            params=servicenow_query_params,
            auth=HTTPBasicAuth(servicenow_username, servicenow_password),
            headers=servicenow_api_headers,
            timeout=30
        )
        
        servicenow_api_response.raise_for_status()
        servicenow_response_data = servicenow_api_response.json()
        
        record_count = len(servicenow_response_data.get("result", []))
        logger.info(f"Retrieved {record_count} records from {table_name}")
        
        return servicenow_response_data
        
    except Timeout:
        logger.error(f"Timeout querying {table_name}")
        raise RequestException("ServiceNow API request timed out")
    except RequestsConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise RequestException(f"Failed to connect to ServiceNow: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        # Parse ServiceNow error response if available
        servicenow_error_message = str(e)
        try:
            servicenow_error_response = servicenow_api_response.json()
            if "error" in servicenow_error_response:
                servicenow_error_detail = servicenow_error_response["error"]
                servicenow_error_message = servicenow_error_detail.get("message", servicenow_error_detail.get("detail", str(e)))
        except (ValueError, KeyError):
            pass  # Use default error message if parsing fails
        
        if servicenow_api_response.status_code == 401:
            raise RequestException("ServiceNow authentication failed. Please check credentials.")
        elif servicenow_api_response.status_code == 403:
            raise RequestException(f"Access denied to table '{table_name}'. Check user permissions.")
        elif servicenow_api_response.status_code == 404:
            raise RequestException(f"Table '{table_name}' not found or access denied.")
        else:
            raise RequestException(f"ServiceNow API error ({servicenow_api_response.status_code}): {servicenow_error_message}")
    except Exception as e:
        logger.error(f"Error querying {table_name}: {e}")
        raise RequestException(f"ServiceNow API request failed: {e}")


def create_service_request(
    sr_config: Dict[str, Any],
    sr_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a Service Request in ServiceNow."""
    logger.info("Creating Service Request in ServiceNow")
    
    servicenow_instance_url = _get_instance_url(sr_config)
    servicenow_username, servicenow_password = _get_credentials()
    
    servicenow_api_path = sr_config.get("servicenow", {}).get("api_path", "/api/now/table")
    table_name = sr_config.get("servicenow", {}).get("table", "sc_request")
    
    servicenow_api_url = f"{servicenow_instance_url}{servicenow_api_path}/{table_name}"
    
    servicenow_api_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        servicenow_api_response = requests.post(
            servicenow_api_url,
            json=sr_data,
            auth=HTTPBasicAuth(servicenow_username, servicenow_password),
            headers=servicenow_api_headers,
            timeout=30
        )
        
        servicenow_api_response.raise_for_status()
        servicenow_response_data = servicenow_api_response.json()
        
        sr_result = servicenow_response_data.get("result", {})
        sr_number = sr_result.get("number", "")
        sys_id = sr_result.get("sys_id", "")
        
        logger.info(f"Created Service Request: {sr_number}")
        
        return {
            "sr_number": sr_number,
            "sys_id": sys_id,
            "result": sr_result
        }
        
    except Timeout:
        logger.error("Timeout creating Service Request")
        raise RequestException("ServiceNow API request timed out")
    except RequestsConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise RequestException(f"Failed to connect to ServiceNow: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error creating SR: {e}")
        servicenow_error_message = str(e)
        try:
            servicenow_error_response = servicenow_api_response.json()
            if "error" in servicenow_error_response:
                servicenow_error_detail = servicenow_error_response["error"]
                servicenow_error_message = servicenow_error_detail.get("message", servicenow_error_detail.get("detail", str(e)))
        except (ValueError, KeyError):
            pass
        
        if servicenow_api_response.status_code == 401:
            raise RequestException("ServiceNow authentication failed. Please check credentials.")
        elif servicenow_api_response.status_code == 403:
            raise RequestException("Access denied. Check user permissions for creating Service Requests.")
        elif servicenow_api_response.status_code == 400:
            raise RequestException(f"Invalid request data: {servicenow_error_message}")
        else:
            raise RequestException(f"ServiceNow API error ({servicenow_api_response.status_code}): {servicenow_error_message}")
    except Exception as e:
        logger.error(f"Error creating Service Request: {e}")
        raise RequestException(f"ServiceNow API request failed: {e}")

