import logging
import json
import sys
import time
import subprocess
from app.domain.models import DocumentBlock, ParsedDocument

class SubprocessMarkerAdapter:
    def __init__(self, cli_script_path: str, timeout_seconds: int  = 300) -> None:
        self.cli_script_data = cli_script_path
        self.timeout_seconds = timeout_seconds

    def parse_file(self, file_path: str, document_id: str) -> ParsedDocument:
        blocks = []
        is_partial = False

        # Start the subprocess to run the CLI script and pass the file instead of file_path as an argument. Capture stdout and stderr.
        process = subprocess.Popen(
            [sys.executable, self.cli_script_data, "--file", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

        start_time = time.time()

        # The Streaming Read loop
        # Iterate over the 'process.stdout' to read the output line by line in real-time
        # Parse the json string into a dictionary.
        # Map the dictionary to the DocumentBlock model and append it to the blocks.
        try:
            for line in process.stdout:
                # Check for timeout
                line = line.strip()
                if not line:
                    continue

                try:
                    block_data = json.loads(line)
                    blocks.append(DocumentBlock(**block_data))
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to decode JSON from line: {line}. Error: {e}")
                    is_partial = True
                    break;

            # The timeout and Exit validation
            # After the loop finishes , call process.wait() to get the final exit code
            process.wait(timeout=self.timeout_seconds)

            if process.returncode != 0:
                logging.error(f"Subprocess exited with code {process.returncode}.")
                is_partial = True

        except subprocess.TimeoutExpired as e:
            process.kill()
            logging.error(f"Timeout expired while waiting for subprocess to finish: {e}")
            is_partial = True

        except Exception as e:
            logging.error(f"An error occurred while processing {file_path}: {e}")
            is_partial = True
        finally:
            if process and process.stdout:
                process.stdout.close()
        

        return ParsedDocument(
            document_id=document_id,
            blocks=blocks,
            is_partial=is_partial
        )

                
