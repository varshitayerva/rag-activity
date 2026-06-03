from typing import List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re


@dataclass
class Chunk:
    text: str
    index: int
    section: Optional[str] = None
    page_number: Optional[int] = None
    token_count: int = 0

    def estimate_tokens(self):
        self.token_count = int(len(self.text.split()) * 1.3)


class Chunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> List[Chunk]:
        pass


class FixedChunker(Chunker):
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[Chunk]:
        words = text.split()
        chunks = []
        chunk_index = 0

        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            if not chunk_words:
                continue

            chunk_text = ' '.join(chunk_words)
            chunk = Chunk(text=chunk_text, index=chunk_index)
            chunk.estimate_tokens()
            chunks.append(chunk)
            chunk_index += 1

        return chunks


class SemanticChunker(Chunker):
    def __init__(self, min_chunk_length: int = 100):
        self.min_chunk_length = min_chunk_length

    def chunk(self, text: str) -> List[Chunk]:
        chunks = []
        chunk_index = 0

        sentences = self._split_sentences(text)
        current_chunk = []
        current_section = None
        page_num = 1

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if self._is_section_header(sentence):
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunk = Chunk(
                        text=chunk_text,
                        index=chunk_index,
                        section=current_section,
                        page_number=page_num
                    )
                    chunk.estimate_tokens()
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = []

                current_section = sentence.replace('#', '').strip()
                current_chunk = [sentence]
            else:
                current_chunk.append(sentence)

                chunk_text = ' '.join(current_chunk)
                if len(chunk_text) > 2000:
                    if len(current_chunk) > 1:
                        chunk_text = ' '.join(current_chunk[:-1])
                        chunk = Chunk(
                            text=chunk_text,
                            index=chunk_index,
                            section=current_section,
                            page_number=page_num
                        )
                        chunk.estimate_tokens()
                        chunks.append(chunk)
                        chunk_index += 1
                        current_chunk = [current_chunk[-1]]

            if sentence.endswith('---'):
                page_num += 1

        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Chunk(
                text=chunk_text,
                index=chunk_index,
                section=current_section,
                page_number=page_num
            )
            chunk.estimate_tokens()
            chunks.append(chunk)

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        text = text.replace('\n', ' ')
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return sentences

    def _is_section_header(self, text: str) -> bool:
        return bool(re.match(r'^#+\s+\w+', text)) or bool(re.match(r'^\d+\.\s+\w+', text))
