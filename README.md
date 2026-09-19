# Multi-Tenant Context Store

A jumpstart project demonstrating how to build a GenAI context storage system for a multi-tenant environment (e.g., Enterprise CRM AI Copilot). It uses **FastAPI** to serve the REST API, **Redis** as a fast first-level cache, and **OpenSearch** as the persistent JSON document store fallback.

## Features

- **Multi-Tenancy**: Data is strictly isolated. Each tenant gets exactly **one dedicated OpenSearch index** (e.g., `tenant-001-context`).
- **Two-Tier Storage**: 
  - **Redis Cache (Tier 1)**: For instantaneous context retrieval.
  - **OpenSearch (Tier 2)**: Persistent, searchable source-of-truth.
- **Resiliency & Self-Healing**: Graceful degradation if Redis crashes, with automatic cache re-warming on restart.
- **Basic Auth Security**: OpenSearch runs with its security plugin enabled out of the box, and Redis is secured via password.
- **Database-Aware Data Models**: Schema models for domains, transactional database tables (`models`), routing, patterns, rules, and examples.
- **Dockerized Setup**: A single `docker-compose.yml` spins up everything you need in seconds.

## Architecture

1. **FastAPI Application**: A Python backend running on port `8001`. 
2. **Redis**: In-memory cache running on `redis:6379` (mapped to `6380` on host).
3. **OpenSearch 2.13**: A single-node cluster mapped to `https://localhost:9201`. 

---

## How Data is Stored (1 Index Per Tenant)

To keep the OpenSearch cluster efficient and easily manageable, **exactly 1 index is created per tenant**. 

Instead of creating separate indices for domains, models, routing, etc., everything for a single tenant is grouped into their dedicated index as separate documents, using a `type` field to distinguish them. 

For example, `tenant-001-context` will contain documents like:
- `{"type": "domains", "data": {...}}`
- `{"type": "models", "data": {...}}`
- `{"type": "routing", "data": {...}}`

## Syncing Strategy (Redis + OpenSearch)

The system is designed to keep Redis and OpenSearch in sync automatically without any background cron jobs, while remaining highly resilient:

- **Reads (Cache-Aside):** The API attempts to fetch the context from Redis first. On a cache miss (or if Redis is offline), it queries OpenSearch, reconstructs the context, and synchronously writes it back to Redis to warm the cache for the next request.
- **Writes (Write-Through):** When context is updated via `POST`, it is written to OpenSearch first. Upon success, it is immediately pushed to Redis. 
- **Graceful Degradation:** If Redis crashes or restarts, the API gracefully catches the connection errors. Reads seamlessly fall back to OpenSearch, and Writes continue to succeed to OpenSearch. Once Redis comes back online, the connection pool automatically recovers and the cache is lazily re-warmed upon the next tenant requests.

---

## Getting Started

### 1. Prerequisites

- Docker and Docker Compose installed on your machine.
- Python 3.10+ (if you want to run the test script locally outside of docker).

### 2. Configure Environment

The project includes a `.env` file containing the OpenSearch credentials, URL, and Redis URL.
```env
OPENSEARCH_URL=https://opensearch:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=Secret_ContextStore99!
REDIS_USER=default
REDIS_PASSWORD=Secret_Redis99!
REDIS_URL=redis://${REDIS_USER}:${REDIS_PASSWORD}@redis:6379/0
```

### 3. Spin up the infrastructure

Start the API, Redis, and OpenSearch containers:

```bash
docker-compose up -d --build
```

### 4. View API Documentation

Once running, navigate to the auto-generated Swagger documentation:

👉 **[http://localhost:8001/docs](http://localhost:8001/docs)**

From there, you can interact directly with the `/tenant/{tenant_id}/context` endpoints.

### 5. View OpenSearch Data Directly

You can query the raw data stored in OpenSearch directly from your browser:
- `https://localhost:9201/tenant-tenant-001-context/_search?pretty`

*(Note: Click through the self-signed certificate warning, and authenticate using `admin` / `Secret_ContextStore99!`)*

### 6. Seed Test Data

We've provided a `test_data.py` script that inserts sample Enterprise CRM contexts for two separate tenants. 

Run it directly inside the FastAPI container:

```bash
docker cp test_data.py fastapi-app:/app/test_data.py
docker exec -e API_URL="http://localhost:8000" fastapi-app python /app/test_data.py
```

---

## Data Schema Example

A typical payload sent to the FastAPI `POST /tenant/{tenant_id}/context` for a CRM application looks like this:

```json
{
  "domains": [
    {"name": "sales", "description": "Global Sales and Lead Management", "attributes": {"region": "North America"}}
  ],
  "models": [
    {
      "name": "crm_leads",
      "description": "Sales Leads and Prospects",
      "fields": [
        {"name": "lead_name", "type": "varchar", "description": "Company or Prospect Name", "required": true},
        {"name": "estimated_revenue", "type": "numeric", "description": "Expected Deal Size", "required": false}
      ]
    }
  ],
  "routing": {
    "strategy": "high_throughput",
    "endpoints": ["https://api.enterprise-ai.local/v1/sales-models"]
  },
  "patterns": [
    {"name": "lead_id_format", "regex": "LID-\\\\d{6}", "description": "Standard Lead ID format"}
  ],
  "rules": [
    {"rule_id": "rule_high_value", "condition": "estimated_revenue > 100000", "action": "route_to_enterprise_queue"}
  ],
  "examples": [
    {"input": "Show me all high value leads", "output": "SELECT * FROM crm_leads WHERE estimated_revenue > 100000;"}
  ]
}
```
