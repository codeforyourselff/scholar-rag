import sys
import json
import re
import select
import signal
import logging
import resource
import subprocess
from app.domain.models import DocumentBlock, DocumentMetaData, ParsedDocument
from app.domain.ports.parser_port import DocumentParserPort

logger = logging.getLogger(__name__)

class SubprocessParserAdapter(DocumentParserPort):
    def __init__(self) -> None:
        pass

    def _extract_bibliography(self, page_texts: list[str]) -> list[str]:
        """Best-effort extraction of bibliography-style references from parsed pages."""
        citations: list[str] = []

        for page_text in page_texts:
            if not page_text:
                continue

            # Common citationish patterns: [1], [Author, Year], and inline URLs.
            for match in re.findall(r"\[[^\]]+\]|https?://\S+", page_text):
                citations.append(match)

        # De-duplicate while preserving order.
        unique_citations: list[str] = []
        for citation in citations:
            if citation not in unique_citations:
                unique_citations.append(citation)

        return unique_citations

    def set_memory_limit(self):
        """Executed by the OS after fork() but before exec()."""
        # 4GB virtual memory limit (4 * 1024 * 1024 * 1024)
        limit = (4 * 1024 * 1024 * 1024)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        except ValueError as e:
            # Fails silently on local Macs, works correctly in your Ubuntu Docker container
            pass

    async def parse_file(self, file_path: str) -> ParsedDocument:
        process = subprocess.Popen(
                [sys.executable, "app/workers/marker_parser.py", "--file", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                preexec_fn=self.set_memory_limit
            )
        
        full_markdown = []
        confidence_scores = []
        idle_timeout = 60.0  # Max seconds we wait for a single page to parse
        
        # 2. Read the JSONL stream without blocking indefinitely
        try:
            while True:
                # select.select waits until stdout has data, or the timeout hits
                reads, _, _ = select.select([process.stdout], [], [], idle_timeout)
                
                if not reads:
                    logger.error(f"Process hung for {idle_timeout}s. Terminating.")
                    process.send_signal(signal.SIGKILL)
                    break
    
                line = process.stdout.readline()
                if not line:
                    break # EOF reached, process finished naturally
    
                # 3. Aggregate the partial results
                try:
                    payload = json.loads(line.strip())
                    
                    # Check for the summary payload at the end
                    if payload.get("status") == "completed":
                        break
                        
                    # Collect valid page markdown
                    if "markdown" in payload and payload.get("status") == "success":
                        full_markdown.append(payload["markdown"])
                        
                    if "confidence" in payload:
                        confidence_scores.append(payload["confidence"])
                        
                except json.JSONDecodeError:
                    logger.warning(f"Ignored non-JSON output: {line.strip()}")
                    continue
    
        finally:
            # Ensure the process is dead and zombies are reaped
            if process.poll() is None:
                process.kill()
            process.wait()
    
        # Evaluate the aftermath
        exit_code:int = process.returncode
        final_markdown = "\n\n".join(full_markdown)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Map to the Document Blocks( Preserving page boundaries)
        blocks: list[DocumentBlock] = []
        for idx, page_text in enumerate(full_markdown):
            blocks.append(DocumentBlock(
                block_id=f"page_{idx + 1}",
                content=page_text,
                type="page" 
            ))

        # Extract citations (Basic regex or placeholder)
        extracted_citations = self._extract_bibliography(full_markdown[-3:])

        if exit_code != 0:
            logger.warning(f"Parser exited abnormally (code {exit_code}). Recovered {len(full_markdown)} pages.")
            # If exit_code is -9, the OS killed it for hitting the 4GB RAM limit.

        # Instantiate the domain entity
        return ParsedDocument(
            document_id=file_path.split("/")[-1],
            metadata=DocumentMetaData(
                confidence_score=avg_confidence,
                pages_recovered=len(full_markdown),
                parser_exit_code=exit_code
            ),
            document_blocks=blocks,
            citations=extracted_citations,
            status="SUCCESS" if exit_code == 0 else "PARTIAL_SUCCESS"
        )