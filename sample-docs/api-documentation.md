---
title: API Documentation
category: API Reference
department: Engineering
---

# API Documentation

## Overview
This document provides comprehensive information about the REST API endpoints and their usage.

## Authentication

### API Key Authentication
All API requests require an API key to be passed in the Authorization header.

Example:
```
Authorization: Bearer your-api-key-here
```

### Rate Limiting
API rate limit is 1000 requests per hour per API key. Exceeding this limit will result in HTTP 429 Too Many Requests.

## Base URL
```
https://api.example.com/v1
```

## Endpoints

### GET /users
Retrieve a list of users.

Query Parameters:
- `limit` (optional): Number of results to return (default: 20, max: 100)
- `offset` (optional): Number of results to skip (default: 0)
- `role` (optional): Filter users by role

Response:
```json
{
  "users": [
    {
      "id": "user123",
      "name": "John Doe",
      "email": "john@example.com",
      "role": "admin"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### POST /users
Create a new user.

Request Body:
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "role": "user"
}
```

Response:
```json
{
  "id": "user456",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "role": "user",
  "created_at": "2024-06-03T10:30:00Z"
}
```

### GET /users/{userId}
Retrieve a specific user by ID.

Response:
```json
{
  "id": "user123",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "admin",
  "created_at": "2024-01-15T08:00:00Z"
}
```

### PUT /users/{userId}
Update user information.

Request Body:
```json
{
  "name": "John Smith",
  "role": "moderator"
}
```

### DELETE /users/{userId}
Delete a user account.

Response:
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

## Error Responses

### HTTP 400 Bad Request
Invalid request parameters.

```json
{
  "error": "Invalid request",
  "message": "Missing required field: email"
}
```

### HTTP 401 Unauthorized
Missing or invalid API key.

```json
{
  "error": "Unauthorized",
  "message": "Invalid API key"
}
```

### HTTP 404 Not Found
Resource not found.

```json
{
  "error": "Not Found",
  "message": "User not found"
}
```

### HTTP 429 Too Many Requests
Rate limit exceeded.

```json
{
  "error": "Rate Limited",
  "message": "Too many requests. Please try again later."
}
```

## Pagination

All list endpoints support pagination using limit and offset parameters.

Example request:
```
GET /users?limit=10&offset=20
```

## Webhook Support

### Register Webhook
POST /webhooks

Request Body:
```json
{
  "url": "https://your-domain.com/webhook",
  "events": ["user.created", "user.updated"]
}
```

### Webhook Events
- `user.created`: Triggered when a new user is created
- `user.updated`: Triggered when a user is updated
- `user.deleted`: Triggered when a user is deleted

## API Versioning
The current API version is v1. Future versions will be indicated by version number in the URL (e.g., /v2).
