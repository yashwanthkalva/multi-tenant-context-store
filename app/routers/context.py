from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..models import TenantContext
from ..opensearch_client import store_full_tenant_context, get_full_tenant_context
from ..redis_client import get_cached_context, set_cached_context

router = APIRouter(
    prefix="/tenant",
    tags=["tenant_context"]
)

@router.post("/{tenant_id}/context", response_model=dict)
def create_tenant_context(tenant_id: str, context: TenantContext, background_tasks: BackgroundTasks):
    try:
        context_dict = context.model_dump()
        
        # 1. Write to OpenSearch (Source of Truth)
        store_full_tenant_context(tenant_id, context_dict)
        
        # 2. Write to Redis (Cache) in sync so it's immediately available
        set_cached_context(tenant_id, context_dict)
        
        return {"status": "success", "message": f"Context stored for tenant {tenant_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tenant_id}/context", response_model=TenantContext)
def get_tenant_context(tenant_id: str):
    try:
        # 1. Try to get from Redis (First Level Cache)
        cached_context = get_cached_context(tenant_id)
        if cached_context:
            print(f"Cache hit for {tenant_id}")
            return TenantContext(**cached_context)
            
        print(f"Cache miss for {tenant_id}, falling back to OpenSearch")
        
        # 2. Fallback to OpenSearch
        context_dict = get_full_tenant_context(tenant_id)
        if not context_dict or not any(context_dict.values()): # checks if all lists are empty
            raise HTTPException(status_code=404, detail=f"Context not found for tenant {tenant_id}")
            
        # 3. Rebuild Cache
        set_cached_context(tenant_id, context_dict)
        
        return TenantContext(**context_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
