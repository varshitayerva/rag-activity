"""Pytest configuration for backend tests."""

import os
import sys

# Set up environment for tests
os.environ['DEMO_MODE'] = 'true'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'postgres'
os.environ['DB_NAME'] = 'fde_rag'
os.environ['GROQ_API_KEY'] = 'sk-test-key'

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)
