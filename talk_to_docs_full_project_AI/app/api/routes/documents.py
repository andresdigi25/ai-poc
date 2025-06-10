from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
from loguru import logger

from app.db.session import get_db
from app.models.document import Document
from app.core.document_processor import DocumentProcessor
from app.core.metrics import API_REQUESTS, API_LATENCY
from app.schemas.document import DocumentResponse, DocumentCreate

router = APIRouter()
document_processor = DocumentProcessor()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""
    try:
        # Save the uploaded file
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document record
        db_document = Document(
            filename=file.filename,
            original_path=file_path,
            status="processing"
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Process the document
        result = await document_processor.process_document(file_path)
        
        # Update document record
        db_document.text_content = result["text_content"]
        db_document.summary = result["summary"]
        db_document.extracted_images = result["images"]
        db_document.metadata = result["metadata"]
        db_document.status = "completed"
        db.commit()
        
        API_REQUESTS.labels(endpoint="/upload", method="POST", status="success").inc()
        return db_document
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        API_REQUESTS.labels(endpoint="/upload", method="POST", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all processed documents."""
    documents = db.query(Document).offset(skip).limit(limit).all()
    API_REQUESTS.labels(endpoint="/", method="GET", status="success").inc()
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        API_REQUESTS.labels(endpoint="/{document_id}", method="GET", status="error").inc()
        raise HTTPException(status_code=404, detail="Document not found")
    
    API_REQUESTS.labels(endpoint="/{document_id}", method="GET", status="success").inc()
    return document 