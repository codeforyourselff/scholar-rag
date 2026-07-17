from app.domain.models import RAGResponseModel
from app.domain.ports.embedder_port import EmbedderPort
from app.domain.ports.llm import LLMPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.modules.rag.prompt_builder import SecurePromptBuilder

class RAGUseCase:
    def __init__(self, vector_port: VectorStorePort, embedding_port: EmbedderPort, llm_port: LLMPort, secure_prompt_builder: SecurePromptBuilder)-> None:
        self.vector_port = vector_port
        self.embedding_port = embedding_port
        self.llm_port = llm_port
        self.secure_prompt_builder = secure_prompt_builder

    async def execute(self,user_query:str)-> RAGResponseModel:
        """Step 1 - Embed the user query using the embedding port."""
        query_embedding: list[float] = self.embedding_port.embed_query(user_query)

        """Step 2 - Retrieve relevant document chunks from the vector store using the query embedding."""
        relevant_chunks= await self.vector_port.search(query=query_embedding,limit=5,MetaData={})

        if relevant_chunks is None or len(relevant_chunks) == 0:
            return RAGResponseModel(answer="I do not have enough context...", used_chunks=[])

        """Step 4 - Construct a secure prompt string. You must explicitly delineate the System Instructions, the Context Data, and the User Question. If you mush them together, you are vulnerable to prompt injection."""
        prompt, used_chunks = self.secure_prompt_builder.build_prompt(user_query=user_query,chunks=relevant_chunks)

        """Step 5 - Use the LLM to generate an answer based on the constructed prompt."""
        result = await self.llm_port.generate_text(prompt=prompt,max_tokens=200)

        return RAGResponseModel(answer=result, used_chunks=used_chunks)