"""User authentication and registration routes."""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from backend.app.database.postgres import db_client
from backend.app.auth import generate_api_key, verify_api_key
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    department: str = "General"


class RegisterResponse(BaseModel):
    username: str
    email: str
    api_key: str
    department: str
    message: str


class LoginRequest(BaseModel):
    api_key: str | None = None
    username: str | None = None
    password: str | None = None
    role: str | None = None  # 'user' or 'admin'
    admin_api_key: str | None = None
    admin_id: str | None = None
    admin_password: str | None = None


class AdminRegisterRequest(BaseModel):
    admin_id: str
    email: str
    password: str


class AdminRegisterResponse(BaseModel):
    admin_id: str
    email: str
    admin_api_key: str
    message: str


@router.post("/register", response_model=RegisterResponse)
async def register_user(request: RegisterRequest):
    """Register a new user and generate API key."""
    try:
        # Validate input
        if not request.username or len(request.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

        if not request.email or "@" not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email format")

        if not request.password or len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        # Generate API key
        api_key = generate_api_key()

        # Hash password (simple hash for demo - use bcrypt in production)
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()

        # Insert into database
        with db_client.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, api_key, department)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username, email, department
                """, (request.username, request.email, password_hash, api_key, request.department))

                result = cursor.fetchone()

                if result:
                    logger.info(f"User registered: {request.username}")
                    return RegisterResponse(
                        username=result[1],
                        email=result[2],
                        api_key=api_key,
                        department=result[3],
                        message="User registered successfully"
                    )
                else:
                    raise HTTPException(status_code=400, detail="Failed to create user")

            except Exception as e:
                if "unique constraint" in str(e).lower():
                    raise HTTPException(status_code=409, detail="Username or email already exists")
                logger.error(f"Registration error: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in register: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
async def login_user(request: LoginRequest):
    """Login with API key or username/password (user or admin)."""
    try:
        with db_client.get_connection() as conn:
            cursor = conn.cursor()

            # ADMIN LOGIN
            if request.role == 'admin':
                # Admin API key login
                if request.admin_api_key:
                    cursor.execute("""
                        SELECT id, admin_id, email, admin_api_key, role
                        FROM admins
                        WHERE admin_api_key = %s AND is_active = true
                    """, (request.admin_api_key,))

                # Admin ID & password login
                elif request.admin_id and request.admin_password:
                    password_hash = hashlib.sha256(request.admin_password.encode()).hexdigest()
                    cursor.execute("""
                        SELECT id, admin_id, email, admin_api_key, role
                        FROM admins
                        WHERE admin_id = %s AND password_hash = %s AND is_active = true
                    """, (request.admin_id, password_hash))
                else:
                    raise HTTPException(status_code=400, detail="Provide either admin API key or admin ID/password")

                result = cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=401, detail="Invalid admin credentials")

                # Update last login for admin
                cursor.execute("""
                    UPDATE admins
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (result[0],))

                logger.info(f"Admin login successful: {result[1]}")
                return {
                    "user_id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "api_key": result[3],
                    "role": result[4],
                    "message": "Admin login successful"
                }

            # USER LOGIN
            else:
                # Login with API key
                if request.api_key:
                    cursor.execute("""
                        SELECT id, username, email, department, role, api_key
                        FROM users
                        WHERE api_key = %s AND is_active = true
                    """, (request.api_key,))

                # Login with username/password
                elif request.username and request.password:
                    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
                    cursor.execute("""
                        SELECT id, username, email, department, role, api_key
                        FROM users
                        WHERE username = %s AND password_hash = %s AND is_active = true
                    """, (request.username, password_hash))
                else:
                    raise HTTPException(status_code=400, detail="Provide either API key or username/password")

                result = cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                # Update last login for user
                cursor.execute("""
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (result[0],))

                logger.info(f"User login successful: {result[1]}")
                return {
                    "user_id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "department": result[3],
                    "role": result[4],
                    "api_key": result[5],
                    "message": "Login successful"
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile")
async def get_profile(request: Request):
    """Get user profile by API key."""
    try:
        api_key = verify_api_key(request)

        with db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, department, role, created_at, last_login
                FROM users
                WHERE api_key = %s AND is_active = true
            """, (api_key,))

            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="User not found")

            return {
                "user": {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "department": result[3],
                    "role": result[4],
                    "created_at": result[5],
                    "last_login": result[6]
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/admin/register")
async def register_admin(request: AdminRegisterRequest):
    """Register a new admin (requires authorization)."""
    try:
        # Validate input
        if not request.admin_id or len(request.admin_id) < 3:
            raise HTTPException(status_code=400, detail="Admin ID must be at least 3 characters")

        if not request.email or "@" not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email format")

        if not request.password or len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        # Generate admin API key
        admin_api_key = generate_api_key()

        # Hash password
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()

        # Insert into database
        with db_client.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO admins (admin_id, email, password_hash, admin_api_key)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, admin_id, email
                """, (request.admin_id, request.email, password_hash, admin_api_key))

                result = cursor.fetchone()

                if result:
                    logger.info(f"Admin registered: {request.admin_id}")
                    return AdminRegisterResponse(
                        admin_id=result[1],
                        email=result[2],
                        admin_api_key=admin_api_key,
                        message="Admin registered successfully"
                    )
                else:
                    raise HTTPException(status_code=400, detail="Failed to create admin")

            except Exception as e:
                if "unique constraint" in str(e).lower():
                    raise HTTPException(status_code=409, detail="Admin ID or email already exists")
                logger.error(f"Admin registration error: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin register: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/profile")
async def get_admin_profile(request: Request):
    """Get admin profile by API key."""
    try:
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")

        with db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, admin_id, email, role, created_at, last_login
                FROM admins
                WHERE admin_api_key = %s AND is_active = true
            """, (api_key,))

            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Admin not found")

            return {
                "admin": {
                    "id": result[0],
                    "admin_id": result[1],
                    "email": result[2],
                    "role": result[3],
                    "created_at": result[4],
                    "last_login": result[5]
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get admin profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/profile")
async def update_profile(request: Request):
    """Update user profile."""
    try:
        api_key = verify_api_key(request)

        # Parse request body
        body = await request.json()

        updates = {}
        if "username" in body:
            updates["username"] = body["username"]
        if "email" in body:
            updates["email"] = body["email"]
        if "department" in body:
            updates["department"] = body["department"]

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Build dynamic update query
        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        values = list(updates.values()) + [api_key]

        with db_client.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(f"""
                    UPDATE users
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE api_key = %s AND is_active = true
                    RETURNING id, username, email, department, role, created_at
                """, values)

                result = cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=404, detail="User not found")

                logger.info(f"User profile updated: {result[1]}")
                return {
                    "user": {
                        "id": result[0],
                        "username": result[1],
                        "email": result[2],
                        "department": result[3],
                        "role": result[4],
                        "created_at": result[5]
                    },
                    "message": "Profile updated successfully"
                }

            except Exception as e:
                if "unique constraint" in str(e).lower():
                    raise HTTPException(status_code=409, detail="Email already in use")
                raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/users")
async def get_all_users(request: Request):
    """Get all users (admin only). Active = logged in within last 24 hours."""
    try:
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")

        # Verify this is an admin
        with db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role FROM admins
                WHERE admin_api_key = %s AND is_active = true
            """, (api_key,))
            admin = cursor.fetchone()

            if not admin:
                raise HTTPException(status_code=403, detail="Admin access required")

            # Get all users with active status based on last_login (within 24 hours)
            cursor.execute("""
                SELECT id, username, email, department, role, is_active, created_at, last_login,
                       (last_login IS NOT NULL AND last_login > NOW() - INTERVAL '24 hours') AS recently_active
                FROM users
                ORDER BY last_login DESC NULLS LAST
            """)

            users = []
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "department": row[3],
                    "role": row[4],
                    "is_active": row[5],
                    "created_at": row[6],
                    "last_login": row[7],
                    "recently_active": row[8]
                })

            logger.info(f"Admin retrieved {len(users)} users")
            return {
                "users": users,
                "total": len(users),
                "active": sum(1 for u in users if u["recently_active"]),
                "inactive": sum(1 for u in users if not u["recently_active"])
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
