from __future__ import annotations

from transformers import AutoTokenizer

from app.domain.models import BlockType, Chunk, DocumentBlock, ParsedDocument


class SemanticMarkdownChunker:
    """Chunk markdown-style parsed documents using the embedding model tokenizer.

    The chunker preserves atomic semantic units for equations and tables so that
    they are never split across chunks, while still enforcing the configured
    chunk-size ceiling for ordinary text.
    """

    def __init__(
        self,
        chunk_size: int = 250,
        chunk_overlap: int = 0,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("The chunk_size is smaller than the chunk_overlap")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def _count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def _page_range(self, pages: list[int]) -> list[int]:
        if not pages:
            return [0]
        return [min(pages), max(pages)]

    def _append_block(self, buffer_parts: list[str], block: DocumentBlock, pages: list[int]) -> None:
        text = block.content.strip()
        if not text:
            return

        if buffer_parts:
            candidate = "\n\n".join(buffer_parts + [text])
            if self._count_tokens(candidate) > self.chunk_size:
                return

        buffer_parts.append(text)
        page_number = block.metadata.get("page_number")
        if isinstance(page_number, int):
            pages.append(page_number)

    def _flush_buffer(
        self,
        buffer_parts: list[str],
        pages: list[int],
        chunks: list[Chunk],
        document_id: str,
        chunk_index: int,
    ) -> int:
        if not buffer_parts:
            return chunk_index

        content = "\n\n".join(buffer_parts).strip()
        if not content:
            return chunk_index

        chunks.append(
            Chunk(
                chunk_id=f"{document_id}_{chunk_index}",
                document_id=document_id,
                content=content,
                token_count=self._count_tokens(content),
                page_range=self._page_range(pages),
            )
        )
        return chunk_index + 1

    def chunk_document(self, document: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        buffer_parts: list[str] = []
        buffer_pages: list[int] = []
        pending_paragraph: DocumentBlock | None = None
        chunk_index = 0

        def flush_current() -> None:
            nonlocal chunk_index
            chunk_index = self._flush_buffer(
                buffer_parts=buffer_parts,
                pages=buffer_pages,
                chunks=chunks,
                document_id=document.document_id,
                chunk_index=chunk_index,
            )
            buffer_parts.clear()
            buffer_pages.clear()

        for block in document.document_blocks:
            if block.type is BlockType.paragraph:
                pending_paragraph = block
                continue

            if pending_paragraph is not None and block.type in {BlockType.equation, BlockType.table}:
                anchor_text = "\n\n".join(
                    [pending_paragraph.content.strip(), block.content.strip()]
                ).strip()
                page_numbers = [
                    page
                    for page in (
                        pending_paragraph.metadata.get("page_number"),
                        block.metadata.get("page_number"),
                    )
                    if isinstance(page, int)
                ]

                candidate_parts = list(buffer_parts)
                if anchor_text:
                    candidate_parts.append(anchor_text)
                candidate = "\n\n".join(candidate_parts).strip()

                if buffer_parts and self._count_tokens(candidate) > self.chunk_size:
                    flush_current()

                if anchor_text:
                    buffer_parts.append(anchor_text)
                    buffer_pages.extend(page_numbers)
                pending_paragraph = None
                continue

            if pending_paragraph is not None:
                paragraph_text = pending_paragraph.content.strip()
                if paragraph_text:
                    paragraph_pages = []
                    page_number = pending_paragraph.metadata.get("page_number")
                    if isinstance(page_number, int):
                        paragraph_pages.append(page_number)

                    candidate_parts = list(buffer_parts)
                    candidate_parts.append(paragraph_text)
                    candidate = "\n\n".join(candidate_parts).strip()

                    if buffer_parts and self._count_tokens(candidate) > self.chunk_size:
                        flush_current()

                    if paragraph_text:
                        buffer_parts.append(paragraph_text)
                        buffer_pages.extend(paragraph_pages)
                pending_paragraph = None

            block_text = block.content.strip()
            if not block_text:
                continue

            candidate_parts = list(buffer_parts)
            candidate_parts.append(block_text)
            candidate = "\n\n".join(candidate_parts).strip()

            if buffer_parts and self._count_tokens(candidate) > self.chunk_size:
                flush_current()

            buffer_parts.append(block_text)
            page_number = block.metadata.get("page_number")
            if isinstance(page_number, int):
                buffer_pages.append(page_number)

        if pending_paragraph is not None:
            paragraph_text = pending_paragraph.content.strip()
            if paragraph_text:
                buffer_parts.append(paragraph_text)
                page_number = pending_paragraph.metadata.get("page_number")
                if isinstance(page_number, int):
                    buffer_pages.append(page_number)

        flush_current()
        return chunks
