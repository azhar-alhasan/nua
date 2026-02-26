from __future__ import annotations


class AgentError(Exception):
    """Base error for agent orchestration failures."""


class ConfigurationError(AgentError):
    """Raised when required configuration is invalid or missing."""


class ToolExecutionError(AgentError):
    """Raised when a tool execution fails in an unrecoverable way."""
