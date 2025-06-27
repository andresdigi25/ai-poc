# FastAPI JWT Authentication

A simple FastAPI application with JWT authentication for secure API access.

## Features

- User registration and login
- JWT token-based authentication
- Protected routes
- Password hashing with bcrypt
- Docker support

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the application
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing with cURL

### 1. Register a new user

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

Response:
```json
{"message": "User registered successfully"}
```

### 2. Login to get JWT token

```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 3. Access protected routes

Replace `YOUR_TOKEN_HERE` with the actual token from the login response:

```bash
# Get protected route
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get user profile
curl -X GET "http://localhost:8000/profile" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Response:
```json
{"message": "Hello testuser, this is a protected route!"}
```

### 4. Test public route

```bash
curl -X GET "http://localhost:8000/"
```

Response:
```json
{"message": "FastAPI JWT Authentication API"}
```

## Complete Example Flow

```bash
# 1. Register user
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secret123"}'

# 2. Login and save token
TOKEN=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secret123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Use token to access protected route
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer $TOKEN"
```

## Configuration

- **Secret Key**: Change `SECRET_KEY` in `auth.py` for production
- **Token Expiry**: Modify `ACCESS_TOKEN_EXPIRE_MINUTES` in `auth.py`
- **Port**: Update port in `docker-compose.yml` or `main.py`

## Security Notes

- Change the secret key in production
- Use environment variables for sensitive configuration
- Implement proper user storage (database) instead of in-memory storage
- Add rate limiting for authentication endpoints
- Use HTTPS in production