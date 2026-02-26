from utils.errors import AgentError, ConfigurationError, ToolExecutionError
from utils.logging import get_logger


def test_logger_factory_returns_named_logger():
    logger = get_logger("nua.test")
    assert logger.name == "nua.test"


def test_error_hierarchy():
    assert issubclass(ConfigurationError, AgentError)
    assert issubclass(ToolExecutionError, AgentError)
