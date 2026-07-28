import uuid
import time
import asyncio
from app.domain.models import BlockType, DocumentBlock, DocumentMetaData, ParsedDocument, SourceType

class MarkerParserAdapter:
    def _run_marker_sync(self, file_path: str)-> dict:
        time.sleep(2)
        return {
        "metadata": {
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks."
        },
        "markdown": "## 1 Introduction\nRecurrent neural networks, long short-term memory and gated recurrent neural networks in particular, have been firmly established as state of the art approaches.\n\n$$ \\text{Attention}(Q, K, V) = \\text{softmax}(\\frac{QK^T}{\\sqrt{d_k}})V $$"
    }
        
    async def parse(self, file_path: str) -> ParsedDocument:
        raw_data = await asyncio.to_thread(self._run_marker_sync, file_path)

        raw_meta = raw_data.get("metadata", {})
        metadata = DocumentMetaData(
            source_id="arxiv:1234",
            source_type=SourceType.PDF,  # Fixed context from input source assumptions
            title=raw_meta.get("title"),
            authors=raw_meta.get("authors", []),
            abstract=raw_meta.get("abstract", "")
        )

        raw_markdown = raw_data.get("markdown", "")
        lines = raw_markdown.split("\n")
        blocks: list[DocumentBlock] = []

        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue
            # Direct mapping logic parsing conditions
            if cleaned_line.startswith("##"):
                block_text = cleaned_line.lstrip("#").strip()
                block_type = BlockType.heading
            elif cleaned_line.startswith("$$"):
                block_text = cleaned_line
                block_type = BlockType.equation
            else:
                block_text = cleaned_line
                block_type = BlockType.paragraph
                
            blocks.append(DocumentBlock(type=block_type, text=block_text))
            
        return ParsedDocument(
            document_id=str(uuid.uuid4()),
            metadata=metadata,
            document_blocks=blocks,
            citations=[]
        )