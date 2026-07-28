from typing import Protocol
from app.domain.models import ParsedDocument

class DocumentParserPort(Protocol):
    async def parse(self, file_path: str) -> ParsedDocument:
        """A single asynchronous method to parse the document"""
        ...