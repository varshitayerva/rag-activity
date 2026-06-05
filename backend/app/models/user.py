"""User models and database operations."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class User:
    """User model."""

    def __init__(self, user_id: str, username: str, email: str, api_key: str,
                 department: str = None, role: str = "user", is_active: bool = True):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.api_key = api_key
        self.department = department
        self.role = role  # 'admin', 'user', 'viewer'
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.last_login = None
        self.search_count = 0
        self.generation_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'department': self.department,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'search_count': self.search_count,
            'generation_count': self.generation_count,
        }


class UserManager:
    """Manage user operations."""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self._init_demo_users()

    def _init_demo_users(self):
        """Initialize demo users."""
        demo_user = User(
            user_id="demo-001",
            username="demo_user",
            email="demo@example.com",
            api_key="sk-demo-key-12345",
            department="Platform",
            role="user"
        )
        self.users["sk-demo-key-12345"] = demo_user

        admin_user = User(
            user_id="admin-001",
            username="admin",
            email="admin@example.com",
            api_key="sk-demo-key-67890",
            department="Admin",
            role="admin"
        )
        self.users["sk-demo-key-67890"] = admin_user

    def create_user(self, username: str, email: str, department: str = None,
                   role: str = "user") -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        api_key = f"sk-{user_id[:12]}"

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            api_key=api_key,
            department=department,
            role=role
        )

        self.users[api_key] = user
        logger.info(f"Created user: {username} ({user_id})")
        return user

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        return self.users.get(api_key)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        for user in self.users.values():
            if user.user_id == user_id:
                return user
        return None

    def record_search(self, api_key: str):
        """Record a search by user."""
        user = self.get_user_by_api_key(api_key)
        if user:
            user.search_count += 1
            user.updated_at = datetime.utcnow()
            logger.info(f"User {user.username} search count: {user.search_count}")

    def record_generation(self, api_key: str):
        """Record a generation by user."""
        user = self.get_user_by_api_key(api_key)
        if user:
            user.generation_count += 1
            user.updated_at = datetime.utcnow()
            logger.info(f"User {user.username} generation count: {user.generation_count}")

    def record_login(self, api_key: str):
        """Record user login."""
        user = self.get_user_by_api_key(api_key)
        if user:
            user.last_login = datetime.utcnow()

    def get_user_stats(self, api_key: str) -> Dict[str, Any]:
        """Get user statistics."""
        user = self.get_user_by_api_key(api_key)
        if not user:
            return {}

        return {
            'username': user.username,
            'department': user.department,
            'role': user.role,
            'search_count': user.search_count,
            'generation_count': user.generation_count,
            'total_queries': user.search_count + user.generation_count,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'member_since': user.created_at.isoformat(),
        }

    def list_users(self, admin_key: str) -> list:
        """List all users (admin only)."""
        admin = self.get_user_by_api_key(admin_key)
        if not admin or admin.role != "admin":
            logger.warning(f"Unauthorized user list access attempt from {admin_key}")
            return []

        return [user.to_dict() for user in self.users.values()]


# Global instance
user_manager = UserManager()
