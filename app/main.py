from fastapi import FastAPI
from .routers import context

app = FastAPI(
    title="Multi-Tenant Context Store",
    description="FastAPI application to store and retrieve tenant context in OpenSearch",
    version="1.0.0"
)

app.include_router(context.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
