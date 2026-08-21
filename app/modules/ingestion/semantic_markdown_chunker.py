import re
from typing import List
from transformers import AutoTokenizer
from app.domain.models import Chunk, ParsedDocument

class SemanticMarkdownChunker:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", max_tokens: int = 250) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.max_tokens = max_tokens
        self.current_buffer: list[dict[str, object]] = []
        self.current_token_count = 0
        self.current_pages: set[int] = set()

    def count_tokens(self, text: str) -> int:
        if not text.strip():
            return 0
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def is_atomic(self, text: str) -> bool:
        text = text.strip()
        is_equation = text.startswith("$$") and text.endswith("$$")
        is_table = bool(re.split(r"\|.*\|", text))
        return is_equation or is_table

    def extract_element(self, markdown_text: str) -> list[str]:
        pattern = r"(#{1,6}\s.*?)(?=\n#|\Z)|(\$\$.*?\$\$)|(\|.*?\|)|([^\n]+)"
        matches = re.findall(pattern, markdown_text, re.DOTALL)
        elements = [match[0] or match[1] or match[2] or match[3] for match in matches if any(match)]
        return elements

    def split_long_paragraph(self, text: str, token_budget: int) -> list[str]:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?]) +", text.strip()) if sentence.strip()]
        return sentences

    def _flush_buffer(self, parsed_document: ParsedDocument, chunks: list[Chunk]) -> None:
        if not self.current_buffer:
            return

        chunk_text = " ".join(item["text"] for item in self.current_buffer if isinstance(item.get("text"), str)).strip()
        if not chunk_text:
            self.current_buffer = []
            self.current_token_count = 0
            self.current_pages.clear()
            return

        page_numbers = sorted(self.current_pages)
        chunk = Chunk(
            chunk_id=f"{parsed_document.document_id}_{len(chunks)}",
            document_id=parsed_document.document_id,
            content=chunk_text,
            token_count=self.current_token_count,
            page_range=page_numbers if page_numbers else [0],
        )
        chunks.append(chunk)
        self.current_buffer = []
        self.current_token_count = 0
        self.current_pages.clear()

    def chunk_document(self, parsed_document: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []

        for block in parsed_document.document_blocks:
            page_number = block.metadata.get("page_number")
            if isinstance(page_number, int):
                self.current_pages.add(page_number)

            elements = self.extract_element(block.content)
            i = 0
            while i < len(elements):
                element = elements[i].strip()
                if not element:
                    i += 1
                    continue

                element_tokens = self.count_tokens(element)
                next_element_tokens = 0
                next_element = ""
                if i + 1 < len(elements):
                    next_element = elements[i + 1].strip()
                    next_element_tokens = self.count_tokens(next_element)

                if self.current_token_count + element_tokens + next_element_tokens > self.max_tokens:
                    if not self.is_atomic(element):
                        split_elements = self.split_long_paragraph(element, self.max_tokens)
                        for split_element in split_elements:
                            split_element_tokens = self.count_tokens(split_element)
                            if self.current_token_count + split_element_tokens > self.max_tokens and self.current_buffer:
                                self._flush_buffer(parsed_document, chunks)
                            self.current_buffer.append({"text": split_element, "page": page_number})
                            self.current_token_count += split_element_tokens
                    else:
                        if self.current_buffer:
                            self._flush_buffer(parsed_document, chunks)
                        self.current_buffer.append({"text": element, "page": page_number})
                        self.current_token_count += element_tokens
                else:
                    self.current_buffer.append({"text": element, "page": page_number})
                    self.current_token_count += element_tokens

                i += 1

        self._flush_buffer(parsed_document, chunks)
        return chunks
