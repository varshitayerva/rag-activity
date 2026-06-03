import io
from typing import List, Tuple
from abc import ABC, abstractmethod
import re

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


class Parser(ABC):
    @abstractmethod
    def parse(self, file_content: bytes) -> Tuple[str, int, dict]:
        pass


class PDFParser(Parser):
    def parse(self, file_content: bytes) -> Tuple[str, int, dict]:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)

        text = ""
        metadata = {
            "page_count": len(reader.pages),
            "has_metadata": reader.metadata is not None
        }

        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num} ---\n{page_text}\n"

        return text, len(reader.pages), metadata


class MarkdownParser(Parser):
    def parse(self, file_content: bytes) -> Tuple[str, int, dict]:
        text = file_content.decode('utf-8', errors='ignore')

        lines = text.split('\n')
        page_count = max(1, len(lines) // 50)

        metadata = {
            "page_count": page_count,
            "has_frontmatter": text.startswith('---')
        }

        return text, page_count, metadata


def get_parser(file_type: str) -> Parser:
    if file_type.lower() in ['pdf', 'application/pdf']:
        return PDFParser()
    elif file_type.lower() in ['markdown', 'text/markdown', 'md']:
        return MarkdownParser()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
