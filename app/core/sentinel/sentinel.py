import subprocess
import resource
import os
import time
import select
import json
import fcntl
from typing import Generator, Dict, Any

def set_memory_limit(max_bytes: int):
    # Set Address Space (Virtual Memory) and Heap Data size limits
    resource.setrlimit(resource.RLIMIT_AS,(max_bytes,max_bytes))
    resource.setrlimit(resource.RLIMIT_DATA,(max_bytes,max_bytes))

def execute_and_monitor(cmd:list,max_memory:int, idle_timeout:int)-> Generator[Dict[str, Any], None, int]:
    """Spawns the subprocess, loops through lines via non-blocking selectors, and yields parsed JSON pages. Yields partial data until crash or exit.Returns the final exit status code."""
    # Spawn subprocess with hard memory boundaries configured in the child context
    process = subprocess.Popen(
        cmd,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=lambda: set_memory_limit(max_memory)
    )

    # Make stdout and stderr file descriptors explicitly non-blocking
    for pipe in (process.stdout, process.stderr):
        if pipe:
            fd = pipe.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    # Initialize monitoring variables
    stdout_buffer = ""
    last_activity_time = time.time()
    
    # Track open streams to read from
    read_set = [process.stdout]

    while read_set:
        # poll every 0.1s to evaluate fine-grained idle timeout and process life
        ready_to_read, _, _ = select.select(read_set, [], [], 0.1)
        current_time = time.time()

        # Check for idle timeout condition
        if (current_time - last_activity_time) > idle_timeout:
            process.kill()
            yield {
                "sentinel_error": "timeout",
                "message": f"Process terminated: Idle timeout of {idle_timeout}s exceeded."
            }
            # Wait for OS cleanup to prevent zombie process
            process.wait()
            return process.returncode

        if process.stdout in ready_to_read:
            try:
                data = process.stdout.read()
                if not data:  # EOF hit
                    read_set.remove(process.stdout)
                else:
                    # Update activity metric since fresh data arrived
                    last_activity_time = current_time
                    stdout_buffer += data
                    
                    # Process lines split by stream newlines
                    while "\n" in stdout_buffer:
                        line, stdout_buffer = stdout_buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                yield {"sentinel_raw_output": line}
            except IOError:
                # No data ready right now (safe to bypass on non-blocking fds)
                pass

        # Check if the process exited outside of standard stream EOF
        if process.poll() is not None:
            # Consume any leftover data stranded in the pipeline buffer
            try:
                remaining_data = process.stdout.read()
                if remaining_data:
                    stdout_buffer += remaining_data
            except IOError:
                pass
            
            # Flush out final residual lines
            if stdout_buffer.strip():
                for line in stdout_buffer.split("\n"):
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            yield {"sentinel_raw_output": line}
            break

    # Read remaining data out of stderr if process crashed out abnormally
    stderr_output = ""
    if process.stderr:
        try:
            stderr_output = process.stderr.read()
        except IOError:
            pass

    # Evaluate return state
    exit_code = process.wait()
    if exit_code != 0:
        yield {
            "sentinel_error": "crash",
            "exit_code": exit_code,
            "stderr": stderr_output.strip() if stderr_output else "None"
        }

    return exit_code

