import os
from urllib.parse import urlparse
from opensearchpy import OpenSearch, helpers

# Initialize OpenSearch client using env vars
os_url = os.environ.get('OPENSEARCH_URL', 'https://localhost:9201')
os_user = os.environ.get('OPENSEARCH_USER', 'admin')
os_password = os.environ.get('OPENSEARCH_PASSWORD', 'Secret_ContextStore99!')

parsed_url = urlparse(os_url)
host = parsed_url.hostname
port = parsed_url.port or 9200
scheme = parsed_url.scheme or 'https'

client = OpenSearch(
    hosts=[{'host': host, 'port': port}],
    http_compress=True,
    http_auth=(os_user, os_password),
    use_ssl=(scheme == 'https'),
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False
)

def get_index_name(tenant_id: str) -> str:
    return f"tenant-{tenant_id}-context"

def create_index_if_not_exists(tenant_id: str):
    index_name = get_index_name(tenant_id)
    if not client.indices.exists(index=index_name):
        index_body = {
            'settings': {
                'index': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0
                }
            },
            'mappings': {
                'properties': {
                    'type': {'type': 'keyword'},
                    'data': {'type': 'object', 'enabled': False} 
                }
            }
        }
        client.indices.create(index=index_name)

def store_full_tenant_context(tenant_id: str, context_dict: dict):
    index_name = get_index_name(tenant_id)
    create_index_if_not_exists(tenant_id)
    
    actions = []
    
    for doc_type, items in context_dict.items():
        if isinstance(items, list):
            for i, item in enumerate(items):
                doc_id = f"{doc_type}_{i}"
                actions.append({
                    "_index": index_name,
                    "_id": doc_id,
                    "_source": {
                        "type": doc_type,
                        "data": item
                    }
                })
        elif isinstance(items, dict):
            actions.append({
                "_index": index_name,
                "_id": doc_type,
                "_source": {
                    "type": doc_type,
                    "data": items
                }
            })
            
    if actions:
        helpers.bulk(client, actions, refresh=True)

def get_full_tenant_context(tenant_id: str) -> dict:
    index_name = get_index_name(tenant_id)
    if not client.indices.exists(index=index_name):
        return None
        
    response = client.search(
        index=index_name,
        body={
            "query": {"match_all": {}},
            "size": 10000
        }
    )
    
    context = {
        "domains": [],
        "models": [],
        "routing": None,
        "patterns": [],
        "rules": [],
        "examples": []
    }
    
    for hit in response['hits']['hits']:
        doc_type = hit['_source']['type']
        data = hit['_source']['data']
        
        if doc_type in ["domains", "models", "patterns", "rules", "examples"]:
            context[doc_type].append(data)
        elif doc_type == "routing":
            context["routing"] = data
            
    return context
