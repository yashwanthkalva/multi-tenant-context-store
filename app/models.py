from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Domain(BaseModel):
    name: str
    description: Optional[str] = None
    attributes: Dict[str, Any] = {}

class ModelField(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False

class DatabaseModel(BaseModel):
    name: str  # e.g., 'account.move'
    description: str
    fields: List[ModelField] = []

class Routing(BaseModel):
    strategy: str
    endpoints: List[str]

class Pattern(BaseModel):
    name: str
    regex: str
    description: Optional[str] = None

class Rule(BaseModel):
    rule_id: str
    condition: str
    action: str

class Example(BaseModel):
    input: str
    output: str

class TenantContext(BaseModel):
    domains: List[Domain] = []
    models: List[DatabaseModel] = []
    routing: Optional[Routing] = None
    patterns: List[Pattern] = []
    rules: List[Rule] = []
    examples: List[Example] = []
