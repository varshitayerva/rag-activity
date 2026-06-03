import pytest
from app.ingestion.parser import PDFParser, MarkdownParser, get_parser


class TestMarkdownParser:
    def setup_method(self):
        self.parser = MarkdownParser()

    def test_parse_basic_markdown(self):
        content = b"# Title\nSome content here."
        text, page_count, metadata = self.parser.parse(content)
        assert "Title" in text
        assert "Some content" in text
        assert page_count > 0

    def test_parse_with_frontmatter(self):
        content = b"---\ntitle: Test\n---\n# Content\nTest content."
        text, page_count, metadata = self.parser.parse(content)
        assert metadata["has_frontmatter"] == True

    def test_parse_without_frontmatter(self):
        content = b"# Content\nTest content."
        text, page_count, metadata = self.parser.parse(content)
        assert metadata["has_frontmatter"] == False

    def test_empty_markdown(self):
        content = b""
        text, page_count, metadata = self.parser.parse(content)
        assert text == ""

    def test_non_utf8_handling(self):
        content = "Test with special chars: café".encode('latin-1')
        text, page_count, metadata = self.parser.parse(content)
        assert text is not None


class TestPDFParser:
    def setup_method(self):
        self.parser = PDFParser()

    def test_parser_initialization(self):
        assert self.parser is not None


class TestGetParser:
    def test_get_markdown_parser(self):
        parser = get_parser("markdown")
        assert isinstance(parser, MarkdownParser)

    def test_get_md_parser(self):
        parser = get_parser("md")
        assert isinstance(parser, MarkdownParser)

    def test_get_text_markdown_parser(self):
        parser = get_parser("text/markdown")
        assert isinstance(parser, MarkdownParser)

    def test_get_pdf_parser(self):
        parser = get_parser("pdf")
        assert isinstance(parser, PDFParser)

    def test_get_application_pdf_parser(self):
        parser = get_parser("application/pdf")
        assert isinstance(parser, PDFParser)

    def test_unsupported_file_type(self):
        with pytest.raises(ValueError):
            get_parser("unsupported_type")
