"""Tests for input validation."""

import pytest
from backend.app.validation import (
    validate_search_query,
    validate_filters,
    validate_file_upload,
    sanitize_filename
)

class TestSearchQueryValidation:
    """Test search query validation."""

    def test_valid_query(self):
        """Valid search query should pass."""
        is_valid, error = validate_search_query("What is Kubernetes?")
        assert is_valid is True
        assert error == ""

    def test_empty_query(self):
        """Empty query should fail."""
        is_valid, error = validate_search_query("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_whitespace_only_query(self):
        """Whitespace-only query should fail."""
        is_valid, error = validate_search_query("   ")
        assert is_valid is False

    def test_query_too_long(self):
        """Query exceeding max length should fail."""
        long_query = "a" * 1000
        is_valid, error = validate_search_query(long_query)
        assert is_valid is False
        assert "character" in error.lower()

    def test_sql_injection_attempt(self):
        """SQL injection patterns should be blocked."""
        is_valid, error = validate_search_query("'; DROP TABLE users; --")
        assert is_valid is False

    def test_non_string_query(self):
        """Non-string query should fail."""
        is_valid, error = validate_search_query(None)
        assert is_valid is False


class TestFiltersValidation:
    """Test filters validation."""

    def test_valid_filters(self):
        """Valid filters should pass."""
        filters = {
            'department': 'Platform',
            'category': 'FAQ',
            'dateFrom': '2026-01-01',
            'dateTo': '2026-12-31',
            'top_k': 10
        }
        is_valid, error = validate_filters(filters)
        assert is_valid is True

    def test_invalid_date_format(self):
        """Invalid date format should fail."""
        filters = {'dateFrom': '01/01/2026'}
        is_valid, error = validate_filters(filters)
        assert is_valid is False

    def test_invalid_top_k(self):
        """Invalid top_k should fail."""
        filters = {'top_k': 200}
        is_valid, error = validate_filters(filters)
        assert is_valid is False

    def test_empty_filters(self):
        """Empty filters dict should be valid."""
        is_valid, error = validate_filters({})
        assert is_valid is True


class TestFileUploadValidation:
    """Test file upload validation."""

    def test_valid_file(self):
        """Valid file should pass."""
        is_valid, error = validate_file_upload("document.txt", 1000)
        assert is_valid is True

    def test_invalid_extension(self):
        """Invalid file extension should fail."""
        is_valid, error = validate_file_upload("malware.exe", 1000)
        assert is_valid is False

    def test_file_too_large(self):
        """Large file should fail."""
        is_valid, error = validate_file_upload("large.pdf", 100_000_000)
        assert is_valid is False

    def test_valid_extensions(self):
        """All valid extensions should pass."""
        for ext in ['.txt', '.pdf', '.md', '.docx']:
            is_valid, _ = validate_file_upload(f"doc{ext}", 1000)
            assert is_valid is True


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_path_traversal_prevention(self):
        """Path traversal attempts should be neutralized."""
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_special_characters_removal(self):
        """Special characters should be removed."""
        result = sanitize_filename("file@#$%name.txt")
        assert "@#$%" not in result

    def test_preserves_valid_chars(self):
        """Valid characters should be preserved."""
        result = sanitize_filename("my-document_v1.txt")
        assert "my-document_v1.txt" == result
