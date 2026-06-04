"""Semantic chunking using RecursiveCharacterTextSplitter without heavy dependencies."""

import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Chunk documents using semantic boundaries (sentences/paragraphs)."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        Initialize semantic chunker.

        Args:
            chunk_size: Target chunk size in characters
            overlap: Character overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into semantic chunks respecting sentence boundaries.

        Args:
            text: Input document text
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dicts with 'text', 'chunk_index', metadata
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided to chunker")
            return []

        try:
            # Implement semantic chunking: split on paragraphs first, then sentences
            chunks = self._semantic_split(text)

            result = []
            for i, chunk_text in enumerate(chunks):
                chunk_dict = {
                    'chunk_index': i,
                    'text': chunk_text.strip(),
                    'section': metadata.get('section') if metadata else None,
                    'page_number': metadata.get('page_number') if metadata else None,
                }
                result.append(chunk_dict)

            logger.info(f"Semantic chunking: split into {len(result)} chunks")
            return result

        except Exception as e:
            logger.error(f"Semantic chunking failed: {e}. Falling back to fixed-size chunking.")
            return self._fallback_fixed_chunking(text, metadata)

    def _semantic_split(self, text: str) -> List[str]:
        """Split text respecting semantic boundaries (paragraphs and sentences)."""
        # Split on double newlines (paragraphs) first
        paragraphs = re.split(r'\n\n+', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # Split paragraph into sentences (simple heuristic: split on . ! ?)
            sentences = re.split(r'(?<=[.!?])\s+', para)

            for sentence in sentences:
                if not sentence.strip():
                    continue

                # If adding this sentence exceeds chunk_size, save current chunk
                if current_chunk and len(current_chunk) + len(sentence) > self.chunk_size:
                    chunks.append(current_chunk.strip())
                    # Add overlap: include last part of previous chunk
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                    current_chunk = overlap_text + " " + sentence
                else:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _fallback_fixed_chunking(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fallback to fixed-size chunking if semantic fails."""
        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Find the next chunk
            end_pos = min(current_pos + self.chunk_size, len(text))

            # Try to break at sentence boundary (. ! ?)
            if end_pos < len(text):
                # Look backward for sentence end
                last_sentence = max(
                    text.rfind('. ', current_pos, end_pos),
                    text.rfind('! ', current_pos, end_pos),
                    text.rfind('? ', current_pos, end_pos)
                )
                if last_sentence > current_pos:
                    end_pos = last_sentence + 2  # Include the period and space

            chunk = text[current_pos:end_pos].strip()
            if chunk:
                chunks.append({
                    'chunk_index': len(chunks),
                    'text': chunk,
                    'section': metadata.get('section') if metadata else None,
                    'page_number': metadata.get('page_number') if metadata else None,
                })

            current_pos = end_pos

        return chunks


class HybridChunker:
    """Choose between semantic and fixed-size chunking at runtime."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.semantic_chunker = SemanticChunker(chunk_size, overlap)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, strategy: str = "semantic",
              metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text using specified strategy.

        Args:
            text: Input document text
            strategy: "semantic" or "fixed"
            metadata: Optional metadata

        Returns:
            List of chunks
        """
        if strategy == "semantic":
            return self.semantic_chunker.chunk(text, metadata)
        else:
            return self._chunk_fixed(text, metadata)

    def _chunk_fixed(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fixed-size chunking (backward compatible)."""
        if not text or len(text.strip()) == 0:
            return []

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            end_pos = min(current_pos + self.chunk_size, len(text))

            # Try to break at space to avoid splitting words
            if end_pos < len(text):
                last_space = text.rfind(' ', current_pos, end_pos)
                if last_space > current_pos:
                    end_pos = last_space

            chunk = text[current_pos:end_pos].strip()
            if chunk:
                chunks.append({
                    'chunk_index': len(chunks),
                    'text': chunk,
                    'section': metadata.get('section') if metadata else None,
                    'page_number': metadata.get('page_number') if metadata else None,
                })

            current_pos = end_pos + 1  # Move past the space

        return chunks
