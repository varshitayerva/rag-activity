"""Pytest configuration and fixtures."""

import sys
from unittest.mock import MagicMock

# Mock external modules before any imports
sys.modules['qdrant_client'] = MagicMock()
sys.modules['qdrant_client.models'] = MagicMock()
sys.modules['openai'] = MagicMock()
