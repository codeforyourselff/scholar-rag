from app.domain.models import EmbeddedChunk

class SecurePromptBuilder:
    def __init__(self,max_token_chars:int = 2000):
        self.max_token_chars = max_token_chars
        self.system_instructions = "You are an AI assistant answering questions based strictly on the provided context. Answer the user's question using ONLY the provided text. If the answer cannot be determined from the context, state 'I do not have enough information in the provided context to answer this question.' Do not use external knowledge."

    def build_prompt(self,chunks:list[EmbeddedChunk])-> tuple[str,list[EmbeddedChunk]]:
        #Construct a secure prompt string. You must explicitly delineate the System Instructions, the Context Data, and the User Question.

        #Step - 1 - Enforce the character limit on the context
        current_length = 0
        context_chunks: list[EmbeddedChunk] = []

        for chunk in chunks:
            formatted_chunk = f"<document>{chunk.text}</document>"
            chunk_length = len(formatted_chunk)

            if current_length + chunk_length > self.max_token_chars:
                break

            context_chunks.append(chunk)
            current_length += chunk_length

        # 2. Join the kept chunks into a single clean string (no Python lists!)
        final_context_str = "\n".join(f"<document>{chunk.text}</document>" for chunk in context_chunks)

        # 3. Assemble the final prompt with clear delineation
        prompt = f"<system>{self.system_instructions}</system>\n<context>\n{final_context_str}\n</context>"
        result: tuple[str,list[EmbeddedChunk]] = (prompt,context_chunks)
        return result
        
