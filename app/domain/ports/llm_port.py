from typing import Protocol

class LLMPort(Protocol):
    """Port for interacting with a large language model (LLM)."""

    async def generate(self, system_prompt: str, user_query: str) -> str:
        """Generate text based on the given prompt."""
        ...

    async def summarize_text(self, text: str) -> str:
        """Summarize the given text."""
        ...

    async def answer_question(self, question: str, context: str) -> str:
        """Answer a question based on the provided context."""
        ...