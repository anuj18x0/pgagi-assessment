import re
import fitz  # PyMuPDF
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PDFLoader:
    def __init__(self, header_margin: float = 50.0, footer_margin: float = 50.0):
        """
        :param header_margin: Height in points from top to ignore as header.
        :param footer_margin: Height in points from bottom to ignore as footer.
        """
        self.header_margin = header_margin
        self.footer_margin = footer_margin

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Extract clean text from PDF bytes handling multi-column layouts and stripping chrome.
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            full_text = []

            for page in doc:
                # Use blocks to handle multi-column layouts correctly
                blocks = page.get_text("blocks")
                page_height = page.rect.height
                
                page_blocks = []
                for b in blocks:
                    # block structure: (x0, y0, x1, y1, "text", block_no, block_type)
                    y0 = b[1]
                    y1 = b[3]
                    
                    # Skip if entirely within header or footer margins
                    if y1 < self.header_margin:
                        continue
                    if y0 > (page_height - self.footer_margin):
                        continue
                    
                    # Extract text from text blocks only (type 0)
                    if b[6] == 0:
                        page_blocks.append(b[4])

                page_text = "\n".join(page_blocks)
                full_text.append(self.normalize_text(page_text))

            return "\n\n".join(full_text)
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            raise

    def normalize_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        """
        # 1. Remove line-break hyphenation
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # 2. Normalize whitespace
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # 3. Strip page numbers
            if re.match(r'^\d+$', line):
                continue
            # Remove redundant internal spaces
            line = " ".join(line.split())
            if line:
                cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)
