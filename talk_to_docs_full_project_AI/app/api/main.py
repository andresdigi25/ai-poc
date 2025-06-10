from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os

from app.core.config import settings
from app.api.routes import documents, health
from app.core.metrics import setup_metrics

app = FastAPI(
    title="Talk to Docs API",
    description="API for processing and analyzing documents",
    version="1.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logger.add(
    os.path.join("logs", "api.log"),
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

# Setup metrics
setup_metrics(app)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Talk to Docs API")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Talk to Docs API") 