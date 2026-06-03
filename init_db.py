#!/usr/bin/env python
"""Initialize database schema."""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.database.postgres import db_client


def main():
    """Initialize database."""
    print("=" * 60)
    print("FDE RAG - Database Initialization")
    print("=" * 60)
    print()

    # Check PostgreSQL connection
    print("[1/3] Checking PostgreSQL connection...")
    try:
        with db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0][:50]}...")
            cursor.close()
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL:")
        print(f"   {e}")
        print()
        print("Make sure PostgreSQL is running:")
        print("  - Check Services: services.msc")
        print("  - Test connection: pg_isready -h localhost -p 5432")
        print()
        return False

    # Initialize database
    print()
    print("[2/3] Creating database schema...")
    success = db_client.init_db()

    if not success:
        print("❌ Failed to initialize database")
        return False

    # Verify tables
    print()
    print("[3/3] Verifying database schema...")
    try:
        with db_client.get_connection() as conn:
            cursor = conn.cursor()

            tables = ['documents', 'chunks', 'metrics', 'search_queries']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} rows")

            cursor.close()
    except Exception as e:
        print(f"❌ Failed to verify schema: {e}")
        return False

    print()
    print("=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Ingest documents: python ingest_sample.py")
    print("2. Start backend: python -m uvicorn backend.main:app --reload")
    print("3. Start frontend: cd frontend && npm run dev")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
