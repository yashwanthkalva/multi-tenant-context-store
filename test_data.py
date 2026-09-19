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
        {"name": "finance", "description": "Financial domain operations", "attributes": {"base_currency": "USD"}}
    ],
    "models": [
        {
            "name": "account.move",
            "description": "Journal Entry / Invoice",
            "fields": [
                {"name": "name", "type": "char", "description": "Invoice Number", "required": True},
                {"name": "amount_total", "type": "monetary", "description": "Total Amount", "required": False}
            ]
        }
    ],
    "routing": {
        "strategy": "lowest_latency",
        "endpoints": ["https://api.openai.com/v1/chat/completions"]
    },
    "patterns": [
        {"name": "invoice_id", "regex": "INV-\\\\d{4}-\\\\d{4}", "description": "Standard invoice ID format"}
    ],
    "rules": [
        {"rule_id": "rule_1", "condition": "user_role == 'admin'", "action": "allow_override"}
    ],
    "examples": [
        {"input": "What is the total revenue?", "output": "SELECT SUM(amount_total) FROM account_move WHERE state = 'posted';"}
    ]
}

tenant2_data = {
    "domains": [
        {"name": "hr", "description": "Human resources domain", "attributes": {"language": "EN"}}
    ],
    "models": [
        {
            "name": "hr.employee",
            "description": "Employee Record",
            "fields": [
                {"name": "name", "type": "char", "description": "Employee Name", "required": True},
                {"name": "department_id", "type": "many2one", "description": "Department", "required": False}
            ]
        }
    ],
    "routing": {
        "strategy": "cost_optimized",
        "endpoints": ["https://api.anthropic.com/v1/messages"]
    },
    "patterns": [
        {"name": "employee_id", "regex": "EMP\\\\d{5}", "description": "Standard employee ID format"}
    ],
    "rules": [
        {"rule_id": "rule_a", "condition": "query_contains('salary')", "action": "require_manager_role"}
    ],
    "examples": [
        {"input": "Who is John Doe's manager?", "output": "SELECT parent_id FROM hr_employee WHERE name = 'John Doe';"}
    ]
}

def seed_data():
    if not wait_for_api():
        return

    print("\\n--- Seeding Tenant 1 ---")
    res1 = requests.post(f"{API_URL}/tenant/tenant-001/context", json=tenant1_data)
    print("Tenant 1 Post Response:", res1.json())

    print("\\n--- Seeding Tenant 2 ---")
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
