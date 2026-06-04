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
    api_key: str = None
    username: str = None
    password: str = None


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
    """Login with API key or username/password."""
    try:
        with db_client.get_connection() as conn:
            cursor = conn.cursor()

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

            # Update last login
            cursor.execute("""
                UPDATE users
                SET last_login = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (result[0],))

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
