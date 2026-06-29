from pathlib import Path
from typing import Iterator
from app.domain.models import DocumentMetaData

class TextStreamingLoader:
    """This class define the document ingestion with chunking protocol"""
    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"Cannot find {self.file_path}")
        if not self.file_path.is_file():
            raise ValueError(f"Path {self.file_path} is not a file")
    
    def get_metadata(self)-> DocumentMetaData:
        return DocumentMetaData(
            source_id= str(self.file_path.absolute()),
            title = None,
            author = None
            )
    
    def stream_file_lines(self,file_path: Path)->Iterator[str]:
        with open(file_path,"r",encoding='utf-8') as file:
            for line in file:
                yield line.rstrip() + " "

    def stream_text(self)-> Iterator[str]:
        for clean_line in self.stream_file_lines(self.file_path):
            yield clean_line




        