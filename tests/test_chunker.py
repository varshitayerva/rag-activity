import pytest
from app.ingestion.chunker import FixedChunker, SemanticChunker


class TestFixedChunker:
    def setup_method(self):
        self.chunker = FixedChunker(chunk_size=500, overlap=100)

    def test_empty_text(self):
        chunks = self.chunker.chunk("")
        assert len(chunks) == 0

    def test_single_word(self):
        chunks = self.chunker.chunk("hello")
        assert len(chunks) == 1
        assert chunks[0].text == "hello"

    def test_basic_chunking(self):
        text = " ".join(["word"] * 600)
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 0
        assert all(chunk.index >= 0 for chunk in chunks)

    def test_chunk_overlap(self):
        text = " ".join([f"word{i}" for i in range(1000)])
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 1
        if len(chunks) > 1:
            chunk1_words = set(chunks[0].text.split())
            chunk2_words = set(chunks[1].text.split())
            overlap = chunk1_words.intersection(chunk2_words)
            assert len(overlap) > 0

    def test_token_estimation(self):
        text = "This is a test sentence with some words."
        chunks = self.chunker.chunk(text)
        for chunk in chunks:
            assert chunk.token_count > 0


class TestSemanticChunker:
    def setup_method(self):
        self.chunker = SemanticChunker(min_chunk_length=100)

    def test_empty_text(self):
        chunks = self.chunker.chunk("")
        assert len(chunks) == 0

    def test_single_sentence(self):
        text = "This is a single sentence."
        chunks = self.chunker.chunk(text)
        assert len(chunks) <= 1

    def test_section_headers(self):
        text = "# Introduction\nThis is the introduction. It contains information.\n## Subsection\nMore content here."
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 0
        assert any(chunk.section is not None for chunk in chunks)

    def test_preserves_boundaries(self):
        text = """
        # Step 1
        This is step one. It has multiple sentences. Each sentence is important.

        # Step 2
        This is step two. It also has multiple sentences. They should stay together.
        """
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 0
        for chunk in chunks:
            assert "Step 1" not in chunk.text or "Step 2" not in chunk.text

    def test_long_text_splitting(self):
        text = " ".join([f"sentence{i}. " for i in range(500)])
        chunks = self.chunker.chunk(text)
        for chunk in chunks:
            assert len(chunk.text) <= 2500

    def test_token_counting(self):
        text = "This is a test sentence with multiple words."
        chunks = self.chunker.chunk(text)
        for chunk in chunks:
            assert chunk.token_count > 0
            word_count = len(chunk.text.split())
            estimated = int(word_count * 1.3)
            assert chunk.token_count == estimated

    def test_special_characters(self):
        text = "Text with special chars: !@#$%^&*() and unicode: café, naïve."
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 0

    def test_non_ascii_handling(self):
        text = "Hello world. Héllo wörld. 你好世界. مرحبا بالعالم."
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 0
