from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    status: str

class DocumentCreate(DocumentBase):
    original_path: str

class DocumentResponse(DocumentBase):
    id: int
    original_path: str
    processed_path: Optional[str] = None
    text_content: Optional[str] = None
    summary: Optional[str] = None
    extracted_images: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 