from app.domain.chunking.semantic_chunker import SemanticMarkdownChunker
from app.domain.models import BlockType, Chunk, DocumentBlock, DocumentMetaData, ParsedDocument


def _block(content: str, block_type: BlockType, page_number: int) -> DocumentBlock:
    return DocumentBlock(
        block_id=f"{block_type.value}-{page_number}",
        type=block_type,
        content=content,
        metadata={"page_number": page_number},
    )


def test_semantic_chunker_tracks_page_span_across_buffer_growth() -> None:
    chunker = SemanticMarkdownChunker(chunk_size=250)
    document = ParsedDocument(
        document_id="doc-1",
        metadata=DocumentMetaData(
            confidence_score=1.0,
            pages_recovered=2,
            parser_exit_code=0,
        ),
        document_blocks=[
            _block("This is page one content.", BlockType.paragraph, 1),
            _block("This is page two content.", BlockType.paragraph, 2),
        ],
    )

    chunks = chunker.chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].page_range == [1, 2]


def test_semantic_chunker_uses_lookahead_anchor_and_preserves_atomic_equation() -> None:
    chunker = SemanticMarkdownChunker(chunk_size=20)
    document = ParsedDocument(
        document_id="doc-2",
        metadata=DocumentMetaData(
            confidence_score=1.0,
            pages_recovered=1,
            parser_exit_code=0,
        ),
        document_blocks=[
            _block("alpha beta gamma delta", BlockType.paragraph, 1),
            _block("$$x = y + z$$", BlockType.equation, 1),
        ],
    )

    chunks = chunker.chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].content.strip().startswith("alpha beta gamma delta")
    assert "$$x = y + z$$" in chunks[0].content
