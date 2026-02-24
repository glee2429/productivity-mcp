"""Structured error handling for the productivity MCP server (Pattern 3)."""

from enum import Enum


class ErrorCode(Enum):
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFLICT = "CONFLICT"
    INTERNAL = "INTERNAL"


class ToolError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def error_response(code: ErrorCode, message: str) -> dict:
    return {"success": False, "error": {"code": code.value, "message": message}}


def success_response(data: dict | list | str) -> dict:
    return {"success": True, "data": data}
