# Multi-Tenant Context Store

A jumpstart project demonstrating how to build a GenAI context storage system for a multi-tenant environment. It uses **FastAPI** to serve the REST API and **OpenSearch** as the vector/JSON document store.

## Features

- **Multi-Tenancy**: Data is strictly isolated. Each tenant gets exactly **one dedicated OpenSearch index** (e.g., `tenant-001-context`).
- **Basic Auth Security**: OpenSearch runs with its security plugin enabled out of the box.
- **Odoo-Aware Data Models**: Schema models for domains, transactional database tables (`models`), routing, patterns, rules, and examples.
- **Dockerized Setup**: A single `docker-compose.yml` spins up everything you need in seconds.

## Architecture

1. **FastAPI Application**: A Python backend running on port `8001`. Exposes endpoints to `POST` and `GET` context for specific tenants.
2. **OpenSearch 2.13**: A single-node cluster mapped to `https://localhost:9201`. Includes basic HTTP authentication.

## How Data is Stored (1 Index Per Tenant)

To keep the OpenSearch cluster efficient and easily manageable, **exactly 1 index is created per tenant**. 

Instead of creating separate indices for domains, models, routing, etc., everything for a single tenant is grouped into their dedicated index as separate documents, using a `type` field to distinguish them. 

For example, `tenant-001-context` will contain documents like:
- `{"type": "domains", "data": {...}}`
- `{"type": "models", "data": {...}}`
- `{"type": "routing", "data": {...}}`

When the API fetches the context, it simply queries all documents in that index and pieces the full payload back together.

## Getting Started

### 1. Prerequisites

- Docker and Docker Compose installed on your machine.
- Python 3.10+ (if you want to run the test script locally outside of docker).

### 2. Configure Environment

The project includes a `.env` file containing the OpenSearch credentials and URL.
```env
OPENSEARCH_URL=https://opensearch:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=Secret_ContextStore99!
```
*Note: The API container connects using `https://opensearch:9200`, but from your host machine you can access OpenSearch at `https://localhost:9201`.*

### 3. Spin up the infrastructure

Start the API and OpenSearch containers:

```bash
docker-compose up -d --build
```

Wait ~30-60 seconds on the first run for OpenSearch to fully initialize its security plugin and start accepting connections.

### 4. View API Documentation

Once running, navigate to the auto-generated Swagger documentation:

👉 **[http://localhost:8001/docs](http://localhost:8001/docs)**

From there, you can interact directly with the `/tenant/{tenant_id}/context` endpoints.

### 5. View OpenSearch Data Directly

You can query the raw data stored in OpenSearch directly from your browser:
- `https://localhost:9201/tenant-001-context/_search?pretty`

*(Note: Click through the self-signed certificate warning, and authenticate using `admin` / `Secret_ContextStore99!`)*

### 6. Seed Test Data

We've provided a `test_data.py` script that inserts sample HR and Finance Odoo contexts for two separate tenants. 

Since the API is running on `8001`, you can run the script from your host machine (assuming you have `requests` installed):

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests
python test_data.py
```

Or run it directly inside the FastAPI container without installing anything locally:

```bash
docker cp test_data.py fastapi-app:/app/test_data.py
docker exec -e API_URL="http://localhost:8000" fastapi-app python /app/test_data.py
```

## Data Schema Example

A typical payload sent to the FastAPI `POST /tenant/{tenant_id}/context` looks like this:

```json
{
  "domains": [
    {"name": "finance", "description": "Financial operations"}
  ],
  "models": [
    {
      "name": "account.move",
      "description": "Journal Entry / Invoice",
      "fields": [
        {"name": "name", "type": "char", "description": "Invoice Number", "required": true}
      ]
    }
  ],
  "routing": {
    "strategy": "lowest_latency",
    "endpoints": ["https://api.openai.com/v1/chat/completions"]
  },
  "patterns": [
    {"name": "invoice_id", "regex": "INV-\\d{4}-\\d{4}"}
  ],
  "rules": [
    {"rule_id": "rule_1", "condition": "user_role == 'admin'", "action": "allow_override"}
  ],
  "examples": [
    {"input": "What is the total revenue?", "output": "SELECT SUM(amount_total) FROM account_move;"}
  ]
}
```
