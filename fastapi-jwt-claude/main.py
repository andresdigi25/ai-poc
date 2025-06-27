from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import uvicorn

from auth import create_access_token, verify_token, get_password_hash, verify_password

app = FastAPI(title="FastAPI JWT Auth", version="1.0.0")
security = HTTPBearer()

# In-memory user store (replace with database in production)
users_db = {}

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if username not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return username

@app.post("/register", response_model=dict)
async def register(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    users_db[user.username] = {"username": user.username, "hashed_password": hashed_password}
    
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    if user.username not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    stored_user = users_db[user.username]
    if not verify_password(user.password, stored_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, this is a protected route!"}

@app.get("/profile")
async def get_profile(current_user: str = Depends(get_current_user)):
    user_data = users_db[current_user]
    return {"username": user_data["username"]}

@app.get("/")
async def root():
    return {"message": "FastAPI JWT Authentication API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)