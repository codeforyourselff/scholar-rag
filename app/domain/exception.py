# Vector-store port custom exception classes
class VectorStoreError(Exception):
    """Root exception for all vector store operations."""


class DimensionMismatchErrors(VectorStoreError):
    """Raised when the vector shape violates the collection's schema."""


class PortUnavailableError(VectorStoreError):
    """Raised when the infrastructure is completely unreachable after retries."""


class PointNotFoundError(VectorStoreError):
    """Raised when attempting to operate on a point ID that does not exist."""

# AI service exception custom exception classes
class AIServiceException(Exception):
    """Base exception for LLM/AI service failures."""
    def __init__(self, message: str = "", *, status_code: int | None = None, error_code: str | None = None, retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.retryable = retryable

class LLMServiceError(AIServiceException):
    """Base exception for LLM API failures."""

class LLMAuthenticationError(LLMServiceError):
    """Raised when the LLM API credentials are invalid."""

class LLMAuthorizationError(LLMServiceError):
    """Raised when the caller lacks permission to use the requested model or resource."""

class LLMValidationError(LLMServiceError):
    """Raised when the request payload or parameters are invalid."""

class LLMRateLimitError(LLMServiceError):
    """Raised when the LLM API rate limit is exceeded."""

class LLMConnectionError(LLMServiceError):
    """Raised when the LLM service cannot be reached."""

class LLMUnexpectedError(LLMServiceError):
    """Raised for unexpected or unclassified LLM failures."""

# Backward-compatible aliases for existing imports.
PortUnavailibleError = PortUnavailableError
PortUnavailibleErrorForAI = LLMUnexpectedError

