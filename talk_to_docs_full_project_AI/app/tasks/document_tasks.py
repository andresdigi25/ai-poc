from app.core.celery_app import celery_app
from app.core.document_processor import DocumentProcessor
from app.db.session import SessionLocal
from app.models.document import Document
from loguru import logger
import os
import time

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    """Process a document asynchronously."""
    try:
        db = SessionLocal()
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        processor = DocumentProcessor()
        result = processor.process_document(document.original_path)
        
        # Update document with results
        document.text_content = result["text_content"]
        document.summary = result["summary"]
        document.extracted_images = result["images"]
        document.metadata = result["metadata"]
        document.status = "completed"
        
        db.commit()
        logger.info(f"Document {document_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        document.status = "failed"
        document.error_message = str(e)
        db.commit()
        
        # Retry the task
        self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes
        
    finally:
        db.close()

@celery_app.task
def cleanup_old_files():
    """Clean up old processed files."""
    try:
        # Delete files older than 30 days
        cleanup_directories = ["uploads", "processed_images"]
        for directory in cleanup_directories:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.getmtime(file_path) < (time.time() - (30 * 24 * 60 * 60)):
                        os.remove(file_path)
                        logger.info(f"Deleted old file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}") 