from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel

RUNTIME_CONTRACT_VERSION = "v1"


class Event(BaseModel):
    method: str
    path: str
    headers: Dict[str, str]
    query: Dict[str, Any]
    body: Optional[bytes]


class Response(BaseModel):
    status_code: int = 200
    headers: Dict[str, str] = {}
    body: Any = None  # JSON serializable


class Context(BaseModel):
    function_id: str
    request_id: str
    contract_version: str = RUNTIME_CONTRACT_VERSION
