from enum import Enum


class LanguageTypes(Enum):
    python = "python"
    go = "go"


class HandlerFiles(Enum):
    python = "handler.py"
    go = "handle.go"
