#!/usr/bin/env python3
"""Initialize admin users in the database."""

import sys
import os
import hashlib
import secrets
import string

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_dir)

from app.database.postgres import db_client

def generate_api_key(length: int = 32) -> str:
    """Generate a secure API key."""
    charset = string.ascii_letters + string.digits + '-'
    return 'admin-sk-' + ''.join(secrets.choice(charset) for _ in range(length))

def init_admins():
    """Initialize demo admin accounts."""
    try:
        # Initialize database schema (creates tables if they don't exist)
        print("Initializing database schema...")
        db_client.init_db()
        print("[OK] Database schema initialized")

        # Demo admin credentials
        demo_admins = [
            {
                'admin_id': 'admin_001',
                'email': 'admin1@rag-system.com',
                'password': 'admin123456',
                'name': 'Admin One'
            },
            {
                'admin_id': 'admin_002',
                'email': 'admin2@rag-system.com',
                'password': 'admin123456',
                'name': 'Admin Two'
            }
        ]

        with db_client.get_connection() as conn:
            cursor = conn.cursor()

            for admin in demo_admins:
                api_key = generate_api_key()
                password_hash = hashlib.sha256(admin['password'].encode()).hexdigest()

                try:
                    cursor.execute("""
                        INSERT INTO admins (admin_id, email, password_hash, admin_api_key)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (admin_id) DO UPDATE SET
                            password_hash = EXCLUDED.password_hash,
                            admin_api_key = EXCLUDED.admin_api_key,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id, admin_id, admin_api_key
                    """, (admin['admin_id'], admin['email'], password_hash, api_key))

                    result = cursor.fetchone()
                    print(f"[OK] Admin '{admin['admin_id']}' initialized")
                    print(f"  - Email: {admin['email']}")
                    print("  - API Key: [REDACTED]")
                    print("  - Password: [REDACTED]")
                    print()

                except Exception as e:
                    if 'unique constraint' in str(e).lower():
                        print(f"[INFO] Admin '{admin['admin_id']}' already exists (skipped)")
                    else:
                        print(f"[ERROR] Error creating admin '{admin['admin_id']}': {e}")

            conn.commit()

        print("\n[SUCCESS] Admin initialization complete!")
        print("\nDemo Admin Accounts:")
        print("=" * 50)
        for admin in demo_admins:
            print(f"Admin ID: {admin['admin_id']}")
            print("Password: [REDACTED]")
            print("-" * 50)

    except Exception as e:
        print(f"[ERROR] Error initializing admins: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_admins()
