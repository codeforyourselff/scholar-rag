import sys
import json
import os
import logging
import warnings

# --- Environment Configuration ---
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# Force CPU Mode
os.environ["TORCH_DEVICE"] = "cpu"
os.environ["OCR_ENGINE"] = "None" 

try:
    import fitz 
    from marker.models import create_model_dict
    from marker.converters.pdf import PdfConverter
    from marker.output import text_from_rendered
except ImportError:
    print(json.dumps({"status": "CRITICAL", "error": "Missing: pip install marker-pdf pymupdf"}))
    sys.exit(1)

class MarkerParserAdapter:
    def __init__(self, mode="fast"):
        self.mode = mode
        self.converter = None  
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(line_buffering=True)

    def _load_resources(self):
        """Loads heavy AI models into memory. Run this ONCE."""
        try:
            model_dict = create_model_dict()
            self.converter = PdfConverter(
                artifact_dict=model_dict,
            )
        except Exception as e:
            self._emit_json({"status": "INIT_FAILED", "error": str(e)})
            sys.exit(1)
        
    def process_file(self, file_path: str):
        if not self.converter:
            self._load_resources()
        
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            self._emit_json({"status": "FILE_ERROR", "error": str(e)})
            sys.exit(1)

        scores = []
        # Stream pages
        for page_idx in range(total_pages):
            result = self._process_single_page(file_path, page_idx, total_pages)
            scores.append(result.get('confidence', 0.0))
            self._emit_json(result)

        # Emit Summary
        self._emit_summary(file_path, scores)

    def _process_single_page(self, pdf_path, page_idx, total_pages):
        """Isolates the risk of a single page crashing the worker."""
        try:
            self.converter.config["page_range"] = [page_idx]
            rendered = self.converter(pdf_path)
            
            # Extract text from the rendered output object
            full_text, _, _ = text_from_rendered(rendered)
            
            conf = self._calculate_confidence(full_text)
            
            return {
                "page": page_idx + 1,
                "total": total_pages,
                "status": "success",
                "confidence": conf,
                "content_preview": full_text[:100].replace("\n", " "),
                "markdown":full_text,
                "length": len(full_text)
            }

        except Exception as e:
            return {
                "page": page_idx + 1,
                "total": total_pages,
                "status": "failed",
                "confidence": 0.0,
                "error": str(e)
            }

    def _calculate_confidence(self, text: str) -> float:
        """Heuristic scoring engine."""
        if not text or len(text.strip()) < 20: return 0.1
        if text.count("") > (len(text) * 0.1): return 0.2
        return 0.95

    def _emit_json(self, data: dict):
        """Centralized output handler."""
        print(json.dumps(data))

    def _emit_summary(self, path, scores):
        avg = sum(scores) / len(scores) if scores else 0.0
        self._emit_json({
            "status": "completed",
            "file": os.path.basename(path),
            "avg_confidence": round(avg, 2)
        })

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to the PDF file")
    args = parser.parse_args()
    adapter = MarkerParserAdapter()
    adapter.process_file(args.file)