from app.domain.exception import (
    AIServiceException,
    OpenAIAuthenticationError,
    OpenAIRateLimitError,
    OpenAIServiceError,
    OpenAIValidationError,
)


def test_ai_service_exception_carries_context() -> None:
    exc = OpenAIAuthenticationError(
        "invalid api key",
        status_code=401,
        error_code="AUTHENTICATION_FAILED",
    )

    assert isinstance(exc, AIServiceException)
    assert isinstance(exc, OpenAIServiceError)
    assert str(exc) == "invalid api key"
    assert exc.status_code == 401
    assert exc.error_code == "AUTHENTICATION_FAILED"


def test_specialized_ai_service_exceptions_are_distinct() -> None:
    rate_limit_error = OpenAIRateLimitError("rate limited", status_code=429)
    validation_error = OpenAIValidationError("bad request", status_code=400)

    assert isinstance(rate_limit_error, OpenAIServiceError)
    assert isinstance(validation_error, OpenAIServiceError)
    assert rate_limit_error.status_code == 429
    assert validation_error.status_code == 400
