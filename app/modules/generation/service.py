from app.domain.models import RAGResponseModel
from app.domain.ports.llm_port import LLMPort
from app.modules.generation.prompt_builder import SecurePromptBuilder
from app.modules.retrieval.service import DocumentRetrievalService

class RAGUseCase:
    def __init__(self, llm_port: LLMPort, service: DocumentRetrievalService, prompt_builder:SecurePromptBuilder)-> None:
        self.service: DocumentRetrievalService = service
        self.llm_port: LLMPort = llm_port
        self.prompt_builder:SecurePromptBuilder = prompt_builder

    async def execute(self, user_query:str, limit: int = 5)-> RAGResponseModel:
        """On the first step we pass the query to the retriveal service"""
        retrieved_chunks = await self.service.execute(user_query=user_query,limit=limit)

        if not retrieved_chunks:
            return RAGResponseModel(answer="No relevant context found in the knowledge base", sources=[])
        
        """Build the single context string from the retrived chunks.."""
        context_string,embedded_chunks = self.prompt_builder.build_prompt(chunks=retrieved_chunks)
        
        """Generate the answer"""
        final_result = await self.llm_port.generate(system_prompt=context_string,user_query=user_query)

        return RAGResponseModel(answer=final_result,sources=embedded_chunks)


