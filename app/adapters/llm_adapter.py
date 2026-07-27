from openai import APIConnectionError, APIStatusError, AsyncOpenAI, AuthenticationError, BadRequestError, PermissionDeniedError, RateLimitError
from app.domain.exception import AIServiceException, LLMAuthenticationError, LLMAuthorizationError, LLMConnectionError, LLMRateLimitError, LLMUnexpectedError, LLMValidationError

class LLMAdapter:
    def __init__(self, client: AsyncOpenAI, model_name: str = "gpt-4o-mini") -> None:
        self.client = client
        self.model_name = model_name

    async def generate(self, system_prompt: str, user_query: str) -> str:
        """Map the system prompt to the provided data."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ],
            )

        except AuthenticationError as exc:
            raise LLMAuthenticationError(
                str(exc),
                status_code=getattr(exc, "status_code", 401),
                error_code="AUTHENTICATION_FAILED",
            ) from exc
        except PermissionDeniedError as exc:
            raise LLMAuthorizationError(
                str(exc),
                status_code=getattr(exc, "status_code", 403),
                error_code="FORBIDDEN",
            ) from exc
        except BadRequestError as exc:
            raise LLMValidationError(
                str(exc),
                status_code=getattr(exc, "status_code", 400),
                error_code="INVALID_REQUEST",
            ) from exc
        except RateLimitError as exc:
            raise LLMRateLimitError(
                str(exc),
                status_code=getattr(exc, "status_code", 429),
                error_code="RATE_LIMITED",
            ) from exc
        except APIConnectionError as exc:
            raise LLMConnectionError(
                str(exc),
                status_code=getattr(exc, "status_code", 503),
                error_code="SERVICE_UNAVAILABLE",
            ) from exc
        except APIStatusError as exc:
            raise LLMUnexpectedError(
                str(exc),
                status_code=getattr(exc, "status_code", 502),
                error_code="LLM_API_ERROR",
            ) from exc
        except Exception as exc:
            raise AIServiceException(str(exc), error_code="LLM_GENERATION_FAILED") from exc

        return response.choices[0].message.content or ""