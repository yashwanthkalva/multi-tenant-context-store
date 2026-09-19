import requests
import json
import time
import os

API_URL = os.environ.get("API_URL", "http://localhost:8001")

def wait_for_api():
    print(f"Waiting for API to be ready at {API_URL}...")
    for _ in range(30):
        try:
            response = requests.get(f"{API_URL}/health")
            if response.status_code == 200:
                print("API is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    print("API not ready after 60 seconds.")
    return False

tenant1_data = {
    "domains": [
        {"name": "sales", "description": "Global Sales and Lead Management", "attributes": {"region": "North America"}}
    ],
    "models": [
        {
            "name": "crm_leads",
            "description": "Sales Leads and Prospects",
            "fields": [
                {"name": "lead_name", "type": "varchar", "description": "Company or Prospect Name", "required": True},
                {"name": "estimated_revenue", "type": "numeric", "description": "Expected Deal Size", "required": False}
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

tenant2_data = {
    "domains": [
        {"name": "customer_support", "description": "Post-sales Support and Ticketing", "attributes": {"region": "Europe"}}
    ],
    "models": [
        {
            "name": "crm_tickets",
            "description": "Customer Support Tickets",
            "fields": [
                {"name": "ticket_subject", "type": "varchar", "description": "Issue Summary", "required": True},
                {"name": "priority", "type": "integer", "description": "Severity Level 1-5", "required": True}
            ]
        }
    ],
    "routing": {
        "strategy": "lowest_latency",
        "endpoints": ["https://api.enterprise-ai.local/v2/support-models"]
    },
    "patterns": [
        {"name": "ticket_id_format", "regex": "TKT-\\\\d{4}-\\\\w{3}", "description": "Standard Ticket ID format"}
    ],
    "rules": [
        {"rule_id": "rule_escalation", "condition": "priority == 1", "action": "notify_support_manager"}
    ],
    "examples": [
        {"input": "Find urgent open tickets", "output": "SELECT ticket_subject FROM crm_tickets WHERE priority = 1 AND status = 'Open';"}
    ]
}

def seed_data():
    if not wait_for_api():
        return

    print("\\n--- Seeding Tenant 1 (AcmeCorp CRM) ---")
    res1 = requests.post(f"{API_URL}/tenant/tenant-001/context", json=tenant1_data)
    print("Tenant 1 Post Response:", res1.json())

    print("\\n--- Seeding Tenant 2 (Globex CRM) ---")
    res2 = requests.post(f"{API_URL}/tenant/tenant-002/context", json=tenant2_data)
    print("Tenant 2 Post Response:", res2.json())
    
    print("\\n--- Waiting for OpenSearch index refresh ---")
    time.sleep(2)
    
    print("\\n--- Fetching Tenant 1 Context ---")
    res1_get = requests.get(f"{API_URL}/tenant/tenant-001/context")
    print(json.dumps(res1_get.json(), indent=2))

    print("\\n--- Fetching Tenant 2 Context ---")
    res2_get = requests.get(f"{API_URL}/tenant/tenant-002/context")
    print(json.dumps(res2_get.json(), indent=2))

if __name__ == "__main__":
    seed_data()
