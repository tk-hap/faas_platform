from pydantic import BaseModel

from .enums import LanguageTypes


class ContainerImage:
    def __init__(self, language: str, tag: str, registry: str):
        self.language = language
        self.tag = tag
        self.registry = registry


class ContainerImageCreate(BaseModel):
    language: LanguageTypes
    body: str
