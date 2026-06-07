"""Database module."""

try:
    from backend.app.database.postgres import PostgresClient, db_client
except ImportError:
    from app.database.postgres import PostgresClient, db_client

__all__ = ['PostgresClient', 'db_client']
