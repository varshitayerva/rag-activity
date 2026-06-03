import pytest
from app.ingestion.metadata import MetadataExtractor
from datetime import datetime


class TestMetadataExtractor:
    def test_basic_extraction(self):
        metadata = MetadataExtractor.extract(
            filename="test.pdf",
            file_type="pdf",
            page_count=10
        )
        assert metadata["filename"] == "test.pdf"
        assert metadata["file_type"] == "pdf"
        assert metadata["page_count"] == 10
        assert metadata["department"] == "General"
        assert metadata["category"] == "Uncategorized"

    def test_extraction_with_department_category(self):
        metadata = MetadataExtractor.extract(
            filename="test.pdf",
            file_type="pdf",
            page_count=10,
            department="Engineering",
            category="Troubleshooting"
        )
        assert metadata["department"] == "Engineering"
        assert metadata["category"] == "Troubleshooting"

    def test_extraction_has_timestamp(self):
        metadata = MetadataExtractor.extract(
            filename="test.pdf",
            file_type="pdf",
            page_count=10
        )
        assert "uploaded_at" in metadata
        assert isinstance(metadata["uploaded_at"], str)

    def test_extraction_with_extra_metadata(self):
        extra = {"custom_field": "custom_value", "another_field": 123}
        metadata = MetadataExtractor.extract(
            filename="test.pdf",
            file_type="pdf",
            page_count=10,
            extra_metadata=extra
        )
        assert metadata["custom_field"] == "custom_value"
        assert metadata["another_field"] == 123

    def test_markdown_file_metadata(self):
        metadata = MetadataExtractor.extract(
            filename="guide.md",
            file_type="markdown",
            page_count=5,
            department="Documentation",
            category="Guide"
        )
        assert metadata["filename"] == "guide.md"
        assert metadata["file_type"] == "markdown"
        assert metadata["page_count"] == 5
