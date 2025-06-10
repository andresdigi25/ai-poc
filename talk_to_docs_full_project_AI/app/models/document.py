from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ARRAY
from sqlalchemy.sql import func
from app.db.base_class import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_path = Column(String)
    processed_path = Column(String, nullable=True)
    status = Column(String)  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Document content
    text_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    topics = Column(ARRAY(String), nullable=True)  # List of main topics
    extracted_images = Column(JSON, nullable=True)  # List of image paths
    
    # LangChain specific
    chunks = Column(ARRAY(Text), nullable=True)  # Document chunks
    embeddings = Column(JSON, nullable=True)  # Vector embeddings
    vector_store_path = Column(String, nullable=True)  # Path to FAISS index
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional metadata like page count, file size, etc.
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Document {self.filename}>" 