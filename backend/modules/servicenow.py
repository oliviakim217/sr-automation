"""
ServiceNow API integration module.

Implements ServiceNow Table API based on official documentation:
https://www.servicenow.com/docs/bundle/xanadu-api-reference/page/integrate/inbound-rest/concept/c_TableAPI.html

Simple module to query ServiceNow tables using the Table API.
"""

import os
import time
import requests
from typing import Dict, Any, Optional, Tuple
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError

from backend.constants import (
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    DEFAULT_JSON_MIME_TYPE,
    DEFAULT_SERVICENOW_API_PATH,
    DEFAULT_SERVICENOW_TABLE,
)
from backend.utils.logger import get_logger

logger = get_logger("sr_automation")


def _get_credentials() -> Tuple[str, str]:
    """Get ServiceNow credentials from environment variables."""
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")
    
    if not username or not password:
        raise ValueError("SERVICENOW_USERNAME and SERVICENOW_PASSWORD must be set")
    
    return username, password


def _get_instance_url(cfg_app_config: Dict[str, Any]) -> str:
    """Get ServiceNow instance URL from config or environment variable."""
    servicenow_instance_url = cfg_app_config.get("servicenow", {}).get("instance_url", "")
    
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
    cfg_app_config: Dict[str, Any],
    table_name: str,
    limit: int = 10
) -> Dict[str, Any]:
    """Query ServiceNow table to retrieve records."""
    client_start_time = time.monotonic()
    record_count: int | None = None
    logger.info(f"BEGIN:fetch_table_records table_name={table_name} limit={limit}")
    
    servicenow_instance_url = _get_instance_url(cfg_app_config)
    servicenow_username, servicenow_password = _get_credentials()
    
    # Get API path from config (defaults to /api/now/table per ServiceNow Table API)
    servicenow_api_path = cfg_app_config.get("servicenow", {}).get("api_path", DEFAULT_SERVICENOW_API_PATH)
    
    servicenow_api_url = f"{servicenow_instance_url}{servicenow_api_path}/{table_name}"
    
    servicenow_query_params_default = cfg_app_config.get("servicenow", {}).get("query_params", {})
    servicenow_query_params = {**servicenow_query_params_default}  # Start with defaults from config
    servicenow_query_params["sysparm_limit"] = limit  # Override with function parameter
    
    servicenow_api_headers = cfg_app_config.get("servicenow", {}).get("headers", {
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
            timeout=DEFAULT_HTTP_TIMEOUT_SECONDS
        )
        
        servicenow_api_response.raise_for_status()
        servicenow_response_json = servicenow_api_response.json()
        
        record_count = len(servicenow_response_json.get("result", []))
        
        return servicenow_response_json
        
    except Timeout:
        logger.error(f"ERROR:fetch_table_records timeout table_name={table_name}")
        raise RequestException("ServiceNow API request timed out")
    except RequestsConnectionError as e:
        logger.error(f"ERROR:fetch_table_records connection_error={e}")
        raise RequestException(f"Failed to connect to ServiceNow: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"ERROR:fetch_table_records http_error={e}")
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
        logger.error(f"ERROR:fetch_table_records unexpected_error={e}")
        raise RequestException(f"ServiceNow API request failed: {e}")
    finally:
        duration_ms = int((time.monotonic() - client_start_time) * 1000)
        logger.info(
            f"END:fetch_table_records table_name={table_name} count={record_count} duration_ms={duration_ms}"
        )


def create_sr(
    cfg_app_config: Dict[str, Any],
    sr_request_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a Service Request in ServiceNow."""
    client_start_time = time.monotonic()
    request_id: str | None = None
    logger.info("BEGIN:create_sr")
    
    servicenow_instance_url = _get_instance_url(cfg_app_config)
    servicenow_username, servicenow_password = _get_credentials()
    
    servicenow_api_path = cfg_app_config.get("servicenow", {}).get("api_path", DEFAULT_SERVICENOW_API_PATH)
    table_name = cfg_app_config.get("servicenow", {}).get("table", DEFAULT_SERVICENOW_TABLE)
    
    servicenow_api_url = f"{servicenow_instance_url}{servicenow_api_path}/{table_name}"
    
    servicenow_api_headers = cfg_app_config.get("servicenow", {}).get("headers", {
        "Accept": "application/json"
    })
    if "Accept" not in servicenow_api_headers:
        servicenow_api_headers["Accept"] = "application/json"
    servicenow_api_headers["Content-Type"] = DEFAULT_JSON_MIME_TYPE
    
    try:
        servicenow_api_response = requests.post(
            servicenow_api_url,
            json=sr_request_payload,
            auth=HTTPBasicAuth(servicenow_username, servicenow_password),
            headers=servicenow_api_headers,
            timeout=DEFAULT_HTTP_TIMEOUT_SECONDS
        )
        
        servicenow_api_response.raise_for_status()
        servicenow_response_json = servicenow_api_response.json()
        
        sr_result = servicenow_response_json.get("result", {})
        request_id = sr_result.get("number", "")
        sys_id = sr_result.get("sys_id", None)
        sys_created_on = sr_result.get("sys_created_on", None)
        sys_updated_on = sr_result.get("sys_updated_on", None)
        opened_at = sr_result.get("opened_at", None)
        state = sr_result.get("state", None)
        approval = sr_result.get("approval", None)
        request_state = sr_result.get("request_state", None)
        stage = sr_result.get("stage", None)
        
        return {
            "request_id": request_id,
            "sys_id": sys_id,
            "sys_created_on": sys_created_on,
            "sys_updated_on": sys_updated_on,
            "opened_at": opened_at,
            "state": state,
            "approval": approval,
            "request_state": request_state,
            "stage": stage,
        }
        
    except Timeout:
        logger.error("ERROR:create_sr timeout")
        raise RequestException("ServiceNow API request timed out")
    except RequestsConnectionError as e:
        logger.error(f"ERROR:create_sr connection_error={e}")
        raise RequestException(f"Failed to connect to ServiceNow: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"ERROR:create_sr http_error={e}")
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
        logger.error(f"ERROR:create_sr unexpected_error={e}")
        raise RequestException(f"ServiceNow API request failed: {e}")
    finally:
        duration_ms = int((time.monotonic() - client_start_time) * 1000)
        logger.info(f"END:create_sr request_id={request_id} duration_ms={duration_ms}")

