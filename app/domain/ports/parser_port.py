from typing import Protocol
from app.domain.models import ParsedDocument

class DocumentParserPort(Protocol):
    def parse_file(self, file_path: str,document_id: str) -> ParsedDocument:
        """A single synchronous method to parse the document"""
        ...