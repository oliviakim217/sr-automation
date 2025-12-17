"""
Application-wide constants.
"""

# HTTP defaults
DEFAULT_HTTP_TIMEOUT_SECONDS = 30

# API validation bounds
API_LIMIT_MIN = 1
API_LIMIT_MAX = 100

# Rate limiting defaults
DEFAULT_RATE_LIMIT_MAX_CALLS_PER_DAY = 1000

# ServiceNow defaults (used only as fallbacks when config is missing)
DEFAULT_SERVICENOW_API_PATH = "/api/now/table"
DEFAULT_SERVICENOW_TABLE = "sc_request"
DEFAULT_JSON_MIME_TYPE = "application/json"


