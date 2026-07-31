import sys
import json
import select
import signal
import subprocess
import resource
import logging
from app.core.celery import celery_app

logger = logging.getLogger(__name__)

def set_memory_limit():
    """Executed by the OS after fork() but before exec()."""
    # 4GB virtual memory limit (4 * 1024 * 1024 * 1024)
    limit = 4 * 1024 * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    except ValueError as e:
        # Fails silently on local Macs, works correctly in your Ubuntu Docker container
        pass

@celery_app.celery.task(bind=True, name="tasks.process_academic_file")
def process_academic_file_task(self, file_path: str, tenant_id: str):
    logger.info(f"Starting isolated parsing for {file_path}")
    
    # 1. Spawn the isolated process
    process = subprocess.Popen(
        [sys.executable, "app/workers/marker_parser.py", "--file", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        preexec_fn=set_memory_limit
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

    # 4. Evaluate the aftermath
    exit_code = process.returncode
    final_markdown = "\n\n".join(full_markdown)
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

    if exit_code != 0:
        logger.warning(f"Parser exited abnormally (code {exit_code}). Recovered {len(full_markdown)} pages.")
        # If exit_code is -9, the OS killed it for hitting the 4GB RAM limit.
        # We still return the partial markdown we managed to save!
    
    return {
        "status": "SUCCESS" if exit_code == 0 else "PARTIAL_SUCCESS",
        "markdown_length": len(final_markdown),
        "pages_recovered": len(full_markdown),
        "confidence": avg_confidence,
        "markdown": final_markdown
    }