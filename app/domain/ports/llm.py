from typing import Protocol
from app.domain.models import RAGResponseModel

class LLMPort(Protocol):
    """Port for interacting with a large language model (LLM)."""

    async def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """Generate text based on the given prompt."""
        ...

    async def summarize_text(self, text: str) -> str:
        """Summarize the given text."""
        ...

    async def answer_question(self, question: str, context: str) -> str:
        """Answer a question based on the provided context."""
        ...