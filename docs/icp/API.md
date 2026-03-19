# API Documentation

Complete reference for all Internet Computer Hosting Platform API endpoints.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Auth Endpoints](#auth-endpoints)
4. [Project Endpoints](#project-endpoints)
5. [Deployment Endpoints](#deployment-endpoints)
6. [Response Formats](#response-formats)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

## Overview

### Architecture: Individual Canisters Per Project

The ICP Hosting Platform uses a **dynamic individual canister model** where:

- **Each project** gets its own unique canister on IC mainnet
- **Each canister** has a unique canister ID and unique URL
- **Complete isolation** between projects for security and independence
- **Direct access** via unique URLs: `https://{CANISTER_ID}.icp0.io`

This differs from a shared canister model. Every project is independently deployed and managed.

### Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://api.example.com` (when deployed)

### API Version

All endpoints use the v1 API: `/api/v1/`

### Available Documentation

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

### Request Format

All requests use JSON:

```
Content-Type: application/json
```

### Response Format

All responses return JSON with the following structure:

```json
{
  "data": { /* response data */ },
  "status": "success|error",
  "message": "Human readable message"
}
```

## Authentication

### JWT Tokens

The API uses JWT (JSON Web Tokens) for authentication.

1. **Obtain Token**: POST to `/api/v1/auth/signup` or `/api/v1/auth/login`
2. **Use Token**: Include in `Authorization` header as `Bearer <token>`
3. **Refresh Token**: POST to `/api/v1/auth/refresh` with refresh token before expiry

### Token Structure

- **Access Token**: Expires in 30 minutes (configurable)
- **Refresh Token**: Expires in 7 days (configurable)
- **Algorithm**: HS256

### Using Tokens

Include in request headers:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Expiration

When access token expires:

```bash
# Use refresh token to get new access token
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <refresh_token>" \
  -d '{}'
```

## Auth Endpoints

### POST /api/v1/auth/signup

Register a new user.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "username": "john_doe"
}
```

**Response** (201 Created):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "john_doe",
    "created_at": "2024-01-15T10:30:00Z",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "status": "success",
  "message": "User registered successfully"
}
```

**Error** (400 Bad Request):
```json
{
  "data": null,
  "status": "error",
  "message": "Email already registered"
}
```

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "username": "john_doe"
  }' | jq
```

---

### POST /api/v1/auth/login

Login with email and password.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "john_doe",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "status": "success",
  "message": "Login successful"
}
```

**Error** (401 Unauthorized):
```json
{
  "data": null,
  "status": "error",
  "message": "Invalid credentials"
}
```

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }' | jq
```

---

### POST /api/v1/auth/refresh

Refresh the access token using a refresh token.

**Request**:
```json
{}
```

**Headers**:
```
Authorization: Bearer <refresh_token>
```

**Response** (200 OK):
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "status": "success",
  "message": "Token refreshed successfully"
}
```

**Error** (401 Unauthorized):
```json
{
  "data": null,
  "status": "error",
  "message": "Invalid or expired refresh token"
}
```

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <refresh_token>" \
  -d '{}' | jq
```

## Project Endpoints

### GET /api/v1/projects

List all projects for the authenticated user.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `skip` (int, optional): Number of items to skip (default: 0)
- `limit` (int, optional): Maximum number of items to return (default: 100)

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "My Portfolio",
      "description": "Personal portfolio website",
      "owner_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Blog",
      "description": "Tech blog and articles",
      "owner_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2024-01-16T11:45:00Z",
      "updated_at": "2024-01-16T11:45:00Z"
    }
  ],
  "status": "success",
  "message": "Projects retrieved successfully"
}
```

**curl Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" | jq
```

---

### POST /api/v1/projects

Create a new project.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "name": "My Portfolio",
  "description": "Personal portfolio website"
}
```

**Response** (201 Created):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "My Portfolio",
    "description": "Personal portfolio website",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "status": "success",
  "message": "Project created successfully"
}
```

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Portfolio",
    "description": "Personal portfolio website"
  }' | jq
```

---

### GET /api/v1/projects/{project_id}

Get details of a specific project.

**Path Parameters**:
- `project_id` (UUID): The project ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "My Portfolio",
    "description": "Personal portfolio website",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "status": "success",
  "message": "Project retrieved successfully"
}
```

**Error** (404 Not Found):
```json
{
  "data": null,
  "status": "error",
  "message": "Project not found"
}
```

**curl Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" | jq
```

---

### PUT /api/v1/projects/{project_id}

Update a project.

**Path Parameters**:
- `project_id` (UUID): The project ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "name": "Updated Portfolio",
  "description": "Updated description"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Updated Portfolio",
    "description": "Updated description",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:45:00Z"
  },
  "status": "success",
  "message": "Project updated successfully"
}
```

**curl Example**:
```bash
curl -X PUT "http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Portfolio",
    "description": "Updated description"
  }' | jq
```

---

### DELETE /api/v1/projects/{project_id}

Delete a project.

**Path Parameters**:
- `project_id` (UUID): The project ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "data": null,
  "status": "success",
  "message": "Project deleted successfully"
}
```

**Error** (404 Not Found):
```json
{
  "data": null,
  "status": "error",
  "message": "Project not found"
}
```

**curl Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" | jq
```

## Deployment Endpoints

### POST /api/v1/deployments/projects/{project_id}/deploy

Deploy a project to a unique individual ICP canister.

This endpoint creates a new canister for the project and deploys HTML content to it.
Each project gets a unique canister ID and unique URL on IC mainnet.

**Path Parameters**:
- `project_id` (int): The project ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "code_content": "<html><body>Hello World</body></html>"
}
```

**Response** (202 Accepted):
```json
{
  "deployment_id": 42,
  "project_id": 5,
  "canister_id": "qjtxq-xaaaa-aaaae-ada4q-cai",
  "url": "https://qjtxq-xaaaa-aaaae-ada4q-cai.icp0.io",
  "status": "deployed",
  "message": "Successfully deployed to https://qjtxq-xaaaa-aaaae-ada4q-cai.icp0.io"
}
```

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/deployments/projects/5/deploy" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code_content": "<html><body>Hello World</body></html>"
  }' | jq
```

---

### POST /api/v1/deployments/projects/{project_id}/update-canister

Update an existing project's canister with new HTML content.

**Path Parameters**:
- `project_id` (int): The project ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request**:
```json
{
  "code_content": "<html><body>Updated Content</body></html>"
}
```

**Response** (200 OK):
```json
{
  "canister_id": "qjtxq-xaaaa-aaaae-ada4q-cai",
  "url": "https://qjtxq-xaaaa-aaaae-ada4q-cai.icp0.io",
  "status": "updated",
  "message": "Canister updated successfully"
}
```

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/deployments/projects/5/update-canister" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code_content": "<html><body>Updated</body></html>"
  }' | jq
```

---

### DELETE /api/v1/deployments/projects/{project_id}/canister

Delete a project's canister from ICP.

**Path Parameters**:
- `project_id` (int): The project ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "Canister qjtxq-xaaaa-aaaae-ada4q-cai deleted successfully",
  "project_id": 5
}
```

**curl Example**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/deployments/projects/5/canister" \
  -H "Authorization: Bearer <access_token>" | jq
```

---

### GET /api/v1/deployments/projects/{project_id}/deployments

Get deployment history for a project.

**Path Parameters**:
- `project_id` (int): The project ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `skip` (int, optional): Number of items to skip (default: 0)
- `limit` (int, optional): Maximum number of items to return (default: 10)

**Response** (200 OK):
```json
[
  {
    "deployment_id": 42,
    "status": "success",
    "message": "Successfully deployed to https://qjtxq-xaaaa-aaaae-ada4q-cai.icp0.io",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:31:00Z"
  }
]
```

**curl Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/deployments/projects/5/deployments" \
  -H "Authorization: Bearer <access_token>" | jq
```

---

### GET /api/v1/deployments/projects/{project_id}/deployments/{deployment_id}

Get details of a specific deployment.

**Path Parameters**:
- `project_id` (int): The project ID
- `deployment_id` (int): The deployment ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "deployment_id": 42,
  "project_id": 5,
  "status": "success",
  "message": "Successfully deployed to https://qjtxq-xaaaa-aaaae-ada4q-cai.icp0.io",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:31:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**curl Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/deployments/projects/5/deployments/42" \
  -H "Authorization: Bearer <access_token>" | jq
```

---

### GET /api/v1/deployments/canisters/{canister_id}/status

Get the current status of a canister.

**Path Parameters**:
- `canister_id` (string): The canister ID

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "status": "running",
  "cycles": 1234567890,
  "memory_usage": 8192
}
```

**curl Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/deployments/canisters/qjtxq-xaaaa-aaaae-ada4q-cai/status" \
  -H "Authorization: Bearer <access_token>" | jq
```

## Response Formats

### Success Response (2xx)

```json
{
  "data": { /* response data or null */ },
  "status": "success",
  "message": "Human readable success message"
}
```

### Error Response (4xx, 5xx)

```json
{
  "data": null,
  "status": "error",
  "message": "Human readable error message"
}
```

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST request |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | User doesn't own resource |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate email/resource |
| 500 | Server Error | Unexpected server error |

### Error Response Example

**Request with missing token**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects"
```

**Response** (401 Unauthorized):
```json
{
  "data": null,
  "status": "error",
  "message": "Not authenticated"
}
```

## Examples

### Complete Workflow: Create User → Create Project → Deploy

```bash
#!/bin/bash

API="http://localhost:8000/api/v1"

# 1. Sign up
SIGNUP=$(curl -s -X POST "$API/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "DemoPassword123!",
    "username": "demo_user"
  }')

TOKEN=$(echo $SIGNUP | jq -r '.data.access_token')
USER_ID=$(echo $SIGNUP | jq -r '.data.id')

echo "✓ User created: $USER_ID"
echo "✓ Token: ${TOKEN:0:20}..."

# 2. Create project
PROJECT=$(curl -s -X POST "$API/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Project",
    "description": "Test deployment"
  }')

PROJECT_ID=$(echo $PROJECT | jq -r '.data.id')
echo "✓ Project created: $PROJECT_ID"

# 3. Create HTML content
HTML_CONTENT='<html>
<head>
  <title>My Project</title>
  <style>
    body { font-family: Arial; text-align: center; margin-top: 50px; }
    h1 { color: #333; }
  </style>
</head>
<body>
  <h1>Hello from Internet Computer!</h1>
  <p>Deployed at: <span id="date"></span></p>
  <script>
    document.getElementById("date").textContent = new Date().toLocaleString();
  </script>
</body>
</html>'

# 4. Deploy project
DEPLOY=$(curl -s -X POST "$API/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"html_content\": $(echo $HTML_CONTENT | jq -Rs .),
    \"network\": \"local\"
  }")

DEPLOYMENT_ID=$(echo $DEPLOY | jq -r '.data.id')
CANISTER_ID=$(echo $DEPLOY | jq -r '.data.canister_id')
DEPLOYMENT_URL=$(echo $DEPLOY | jq -r '.data.deployment_url')

echo "✓ Deployment created: $DEPLOYMENT_ID"
echo "✓ Canister ID: $CANISTER_ID"
echo "✓ Access at: $DEPLOYMENT_URL"

# 5. Get deployment status
curl -s -X GET "$API/deployments/$DEPLOYMENT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.data'
```

### Using jq for Response Parsing

Extract specific fields from responses:

```bash
# Get access token
curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq -r '.data.access_token'

# List all projects
curl -s -X GET "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer <token>" | jq '.data | length'

# Pretty print response
curl -s -X GET "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer <token>" | jq '.'
```

---

**Interactive API Documentation**: http://localhost:8000/docs (when running locally)
