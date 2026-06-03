"""Input validation utilities."""

from typing import Dict, Any
import re
from datetime import datetime

def validate_search_query(query: str, max_length: int = 500) -> tuple[bool, str]:
    """Validate search query."""
    if not query or not isinstance(query, str):
        return False, "Query must be a non-empty string"

    if len(query.strip()) == 0:
        return False, "Query cannot be empty"

    if len(query) > max_length:
        return False, f"Query must be under {max_length} characters"

    # Prevent SQL injection patterns
    dangerous_patterns = [r"'.*OR.*'", r"DROP\s+TABLE", r"DELETE\s+FROM", r";.*--"]
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Invalid query format"

    return True, ""

def validate_filters(filters: Dict[str, Any]) -> tuple[bool, str]:
    """Validate search filters."""
    if not filters:
        return True, ""

    # Validate department
    if 'department' in filters:
        dept = filters['department']
        if dept and (not isinstance(dept, str) or len(dept) > 100):
            return False, "Invalid department filter"

    # Validate category
    if 'category' in filters:
        cat = filters['category']
        if cat and (not isinstance(cat, str) or len(cat) > 100):
            return False, "Invalid category filter"

    # Validate dates
    if 'dateFrom' in filters:
        if not _validate_date(filters['dateFrom']):
            return False, "Invalid dateFrom format (use YYYY-MM-DD)"

    if 'dateTo' in filters:
        if not _validate_date(filters['dateTo']):
            return False, "Invalid dateTo format (use YYYY-MM-DD)"

    # Validate top_k
    if 'top_k' in filters:
        try:
            top_k = int(filters['top_k'])
            if top_k < 1 or top_k > 100:
                return False, "top_k must be between 1 and 100"
        except (ValueError, TypeError):
            return False, "top_k must be an integer"

    return True, ""

def _validate_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)."""
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_file_upload(filename: str, file_size: int, max_size: int = 50_000_000) -> tuple[bool, str]:
    """Validate file upload."""
    if not filename or len(filename) > 255:
        return False, "Invalid filename"

    if file_size > max_size:
        return False, f"File size exceeds {max_size / 1_000_000:.0f}MB limit"

    # Allowed extensions
    allowed = {'.txt', '.pdf', '.md', '.docx'}
    ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''

    if ext not in allowed:
        return False, f"File type not allowed. Allowed: {', '.join(allowed)}"

    return True, ""

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    # Remove special characters
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    return filename
