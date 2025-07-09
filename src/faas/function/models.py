from datetime import datetime
from pydantic import BaseModel

class FunctionCreate(BaseModel):
    language: str
    body: str

class FunctionResponse(BaseModel):
    id: str
    language: str
    url: str
    created_at: datetime