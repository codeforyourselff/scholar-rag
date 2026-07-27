from app.domain.ports.llm_port import LLMPort

class FakeLLMAdapter(LLMPort):
    def __init__(self) -> None:
        pass

    async def generate(self, system_prompt: str, user_query: str)-> None:
        """Pass the user queyr with the given system prompt"""
        pass
        