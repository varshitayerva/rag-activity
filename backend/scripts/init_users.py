#!/usr/bin/env python3
"""Initialize demo user."""

import sys
import os
import hashlib

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_dir)

from app.database.postgres import db_client
from app.auth import generate_api_key

def init_users():
    """Initialize demo user account."""
    try:
        api_key = generate_api_key()
        password_hash = hashlib.sha256('password123'.encode()).hexdigest()

        with db_client.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, api_key, department, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        api_key = EXCLUDED.api_key,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id, username, api_key
                """, ('demouser', 'demo@example.com', password_hash, api_key, 'General', 'user'))

                result = cursor.fetchone()
                print("[OK] Demo user 'demouser' initialized")
                print(f"  - Email: demo@example.com")
                print(f"  - API Key: {api_key}")
                print(f"  - Password: password123")

            except Exception as e:
                print(f"[ERROR] Error creating user: {e}")

            conn.commit()

        print("\n[SUCCESS] Demo user initialized!")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_users()
