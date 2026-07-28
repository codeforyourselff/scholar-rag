from app.domain.ports.llm_port import LLMPort

class FakeLLMAdapter:
    def __init__(self) -> None:
        pass

    async def generate(self, system_prompt: str, user_query: str)-> str:
        return "This is a mocked rag response from the FakeLLMAdapter"