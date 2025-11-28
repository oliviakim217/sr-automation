# SR Automation Service

A Python FastAPI backend for creating Service Requests in ServiceNow.

- FastAPI backend receives JSON payloads from bots or other clients.
- Validates, transforms, and enriches input before sending to ServiceNow REST API.
- Uses environment variables and YAML config files for flexible deployment.
- Supports development and production environments.
- Credentials and ServiceNow URLs are never hardcoded; always use environment variables.

## Setup

1. Create a `.env` file in the project root with your ServiceNow credentials:
   - Copy `.env.sample` to `.env`
   - Fill in your actual ServiceNow credentials
   ```
   SERVICENOW_INSTANCE_URL=your-instance.service-now.com
   SERVICENOW_USERNAME=your_username
   SERVICENOW_PASSWORD=your_password
   SERVICENOW_ENVIRONMENT=dev
   ```

2. Install dependencies: `pip install -r requirements.txt`

3. Run the service: `uvicorn backend.main:app --reload`
