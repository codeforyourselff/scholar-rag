import os
import sys
import json
import argparse
import logging
import warnings
import time
import traceback

# Silence the noise
warnings.filterwarnings('always')

def stderr_warn(message,category,filename,lineno,file=None,line=None):
    sys.stderr.write(warnings.formatwarning(message=message,category=category,filename=filename,lineno=lineno,line=line))

warnings.showwarning = stderr_warn
logging.basicConfig(stream=sys.stderr,level=logging.WARNING,force=True)
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
logger = logging.getLogger("document_processor")
logger.setLevel(logging.INFO) 
handler = logging.StreamHandler(sys.stderr)
logger.propagate = False
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def process_file(file_path: str) -> None: 
    """Simulate the ML model parsing a document page by page..."""

    # Input validations
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Cannot find pdf file at {file_path}")

    # Simulate ML Model Initialization
    logger.info(f"Initializing ML models for processing...")
    time.sleep(0.5)

    # Trigger a mock warning to demonstrate it routes safetly to stderr
    warnings.warn("CUDA is not availible.Falling back to CPU execution.",RuntimeWarning)

    #Process Document Structure
    total_pages = 3
    logger.info(f"Starting pipeline processing. Total pages discovered: {total_pages}")

    for page_num in range(1,total_pages + 1):
        logger.info(f"-> Processing page {page_num}/{total_pages}...")
        time.sleep(0.8)

        if page_num == 2:
            logger.warning(f"Transformer attention weights dropped below threshold on page {page_num}.")
        
        parsed_page = {
            "page_number":page_num,
            "markdown":f"# page{ page_num}\nThis is the simulated extracted markdown text content for page {page_num}",
            "metadata":{
                "word_count": 15 + page_num,
                "confidence_score":0.98
            }
        }

        json_output = json.dumps(parsed_page)
        sys.stdout.write(json_output + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--file",type=str,required=True,help="Path to the PDF file that needs to be processed")
    args=parser.parse_args()

    try:
        process_file(args.file)
    except Exception as e:
        sys.stderr.write(f"ERROR: ML model pipeline crashed while processing file.\n")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)