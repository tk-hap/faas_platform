from typing import Literal
from pydantic import BaseModel

class ContainerImage:
    def __init__(self, language: str, tag: str, registry: str):
        self.language = language
        self.tag = tag
        self.registry = registry

class ContainerImageCreate(BaseModel):
    language: Literal["python"]
    body: str

    
