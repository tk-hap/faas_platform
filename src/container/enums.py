from enum import StrEnum


class LanguageTypes(StrEnum):
    python = "python"
    go = "go"


class HandlerFiles(StrEnum):
    python = "handler.py"
    go = "handle.go"
