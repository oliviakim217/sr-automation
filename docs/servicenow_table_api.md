---
title: "ServiceNow Table API (Reference)"
source: "Official ServiceNow documentation"
purpose: "Internal reference for this project"
---

## Official documentation

- [ServiceNow Table API (Xanadu)](https://www.servicenow.com/docs/bundle/xanadu-api-reference/page/integrate/inbound-rest/concept/c_TableAPI.html)

## How this project uses the Table API

- **Read records (GET)**: `GET {instance}{api_path}/{table_name}`
- **Create SR (POST)**: `POST {instance}{api_path}/{table_name}` (this project defaults to `sc_request`)

## Authentication (Auth)

- **Basic Auth (current POC)**: username/password (stored in env vars).
  - `SERVICENOW_USERNAME`
  - `SERVICENOW_PASSWORD`
- **OAuth / Bearer token (common in prod)**: preferred for production in many orgs.
  - If you add OAuth later, you typically send `Authorization: Bearer <token>`

## Headers

- **GET**: `Accept: application/json`
- **POST**: `Accept: application/json`, `Content-Type: application/json`

## Common Table API query parameters (sysparm_*)

These go on the query string, e.g. `...?sysparm_limit=10&sysparm_offset=0`.

- **`sysparm_query`**: filter using an *encoded query*
  - Example: `active=true^priority=1`
- **`sysparm_limit`**: max rows returned
- **`sysparm_offset`**: skip N rows (pagination)
- **`sysparm_fields`**: return only specific fields
  - Example: `number,short_description,sys_id`
- **`sysparm_display_value`**: how reference fields are returned
  - `false` = raw values (often sys_ids)
  - `true` = display values
  - `all` = both (can increase payload size)
- **`sysparm_exclude_reference_link`**: `true` removes reference “link” objects from the response
- **`sysparm_order_by` / `sysparm_order_by_desc`**: sort results
  - Example: `sysparm_order_by_desc=sys_created_on`

### Encoded query tip

Instead of hand-writing complex queries, build a filter in the ServiceNow list UI and “copy query” (encoded query), then paste it into `sysparm_query`.

## Response format (success)

- ServiceNow typically returns JSON containing a top-level **`result`**.
  - For **GET**, `result` is usually a list of records.
  - For **POST**, `result` is usually the created record.

### Reference samples in this repo

- GET sample: `reference/servicenow_get_sc_request_sample_response.json`
- POST sample: `reference/servicenow_post_sc_request_sample_response.json`

## Error format (common shape)

ServiceNow errors commonly look like:

```json
{
  "error": {
    "message": "....",
    "detail": "...."
  },
  "status": "failure"
}
```

## Naming policies (this repo)

- **Internal Python names**: `snake_case` (variables/functions) and `PascalCase` (classes).
- **ServiceNow field names**: keep **exact ServiceNow field names** in payloads/requests (example: `short_description`, `assigned_to`).
- **API vs Client function naming**: FastAPI handlers start with `api_`; ServiceNow client functions stay clean (see `.cursor/rules/naming-rules.mdc`).

## Project config pointers

- `configs/<env>/servicenow.yaml` controls defaults like:
  - `servicenow.api_path`
  - `servicenow.table`
  - `servicenow.query_params` (your default `sysparm_*` values)


