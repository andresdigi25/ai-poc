from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import pandas as pd
import json
from datetime import datetime
import logging
from io import BytesIO
import os

# Import our modules
from config import settings, ensure_directories
from database import get_db, init_db, get_db_stats, backup_db, cleanup_old_logs
from models import CoTMapping, ProcessingLog, EmailConfig, SystemSettings
from email_processor import email_processor
from chat_handler import CoTChatbot

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
ensure_directories()

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

# Create FastAPI app
app = FastAPI(
    title="CoT Mapping Email System",
    description="Automated Class of Trades mapping system with email processing and AI chat",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

# Templates
templates = Jinja2Templates(directory=settings.template_dir)

# Initialize chatbot
chatbot = CoTChatbot()

# Pydantic models for API
from pydantic import BaseModel

class CoTMappingResponse(BaseModel):
    id: int
    ic_channel: Optional[str]
    ic_cot: Optional[str]
    new_channel: Optional[str]
    new_cot: Optional[str]
    notes: Optional[str]
    source_file: Optional[str]
    is_new_channel: bool
    is_new_cot: bool
    processed_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProcessingLogResponse(BaseModel):
    id: int
    file_name: Optional[str]
    email_sender: Optional[str]
    total_records: int
    new_channels_found: int
    new_cots_found: int
    records_inserted: int
    records_updated: int
    processing_status: str
    processed_at: datetime
    
    class Config:
        from_attributes = True

class EmailConfigResponse(BaseModel):
    imap_server: str
    imap_port: int
    email_username: Optional[str]
    smtp_server: str
    smtp_port: int
    enabled: bool
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    question: str
    answer: str
    timestamp: datetime

# Utility functions
class CoTProcessor:
    """Main CoT processing logic"""
    
    @staticmethod
    def identify_new_items(df: pd.DataFrame, db: Session) -> Dict[str, List[str]]:
        """Identify new channels and COTs"""
        
        # Get existing values
        existing_channels = set(
            row[0] for row in db.query(CoTMapping.new_channel).distinct().all()
            if row[0] is not None
        )
        existing_cots = set(
            row[0] for row in db.query(CoTMapping.new_cot).distinct().all()
            if row[0] is not None
        )
        
        # Get values from file
        file_channels = set(df['new_channel'].dropna().unique())
        file_cots = set(df['new_cot'].dropna().unique())
        
        # Find new items
        new_channels = list(file_channels - existing_channels)
        new_cots = list(file_cots - existing_cots)
        
        logger.info(f"Found {len(new_channels)} new channels, {len(new_cots)} new COTs")
        
        return {
            'new_channels': new_channels,
            'new_cots': new_cots
        }
    
    @staticmethod
    def process_excel_data(df: pd.DataFrame, source_file: str, db: Session) -> Dict[str, Any]:
        """Process Excel data and update database"""
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Map columns
        column_mapping = {
            'ic channel': 'ic_channel',
            'ic cot': 'ic_cot',
            'new channel': 'new_channel',
            'new cot': 'new_cot',
            'notes': 'notes'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Validate required columns
        required_columns = ['ic_channel', 'ic_cot', 'new_channel', 'new_cot']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Identify new items
        new_items = CoTProcessor.identify_new_items(df, db)
        
        records_inserted = 0
        records_updated = 0
        records_skipped = 0
        
        for _, row in df.iterrows():
            try:
                # Skip rows with missing required data
                if pd.isna(row.get('ic_channel')) or pd.isna(row.get('ic_cot')):
                    records_skipped += 1
                    continue
                
                # Check if mapping exists
                existing = db.query(CoTMapping).filter(
                    CoTMapping.ic_channel == row.get('ic_channel'),
                    CoTMapping.ic_cot == row.get('ic_cot')
                ).first()
                
                is_new_channel = row.get('new_channel') in new_items['new_channels']
                is_new_cot = row.get('new_cot') in new_items['new_cots']
                
                if existing:
                    # Update existing
                    existing.new_channel = row.get('new_channel')
                    existing.new_cot = row.get('new_cot')
                    existing.notes = row.get('notes')
                    existing.is_new_channel = is_new_channel
                    existing.is_new_cot = is_new_cot
                    existing.source_file = source_file
                    existing.processed_date = datetime.utcnow()
                    existing.updated_at = datetime.utcnow()
                    records_updated += 1
                else:
                    # Create new
                    new_mapping = CoTMapping(
                        ic_channel=row.get('ic_channel'),
                        ic_cot=row.get('ic_cot'),
                        new_channel=row.get('new_channel'),
                        new_cot=row.get('new_cot'),
                        notes=row.get('notes'),
                        source_file=source_file,
                        is_new_channel=is_new_channel,
                        is_new_cot=is_new_cot
                    )
                    db.add(new_mapping)
                    records_inserted += 1
                    
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                records_skipped += 1
                continue
        
        db.commit()
        
        return {
            'total_records': len(df),
            'records_inserted': records_inserted,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'new_channels_found': len(new_items['new_channels']),
            'new_cots_found': len(new_items['new_cots']),
            'new_channels': new_items['new_channels'],
            'new_cots': new_items['new_cots']
        }

# Routes

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Excel Processing Endpoints

@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process Excel file"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        # Read file content
        content = await file.read()
        
        # Save file
        file_path = os.path.join(settings.upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process Excel
        df = pd.read_excel(BytesIO(content))
        result = CoTProcessor.process_excel_data(df, file.filename, db)
        
        # Create processing log
        log = ProcessingLog(
            file_name=file.filename,
            email_sender="manual_upload",
            total_records=result['total_records'],
            new_channels_found=result['new_channels_found'],
            new_cots_found=result['new_cots_found'],
            records_inserted=result['records_inserted'],
            records_updated=result['records_updated'],
            records_skipped=result['records_skipped'],
            processing_status='SUCCESS',
            file_size_bytes=len(content),
            new_channels_list=result['new_channels'],
            new_cots_list=result['new_cots']
        )
        db.add(log)
        db.commit()
        
        logger.info(f"Successfully processed {file.filename}")
        
        return {
            "message": "File processed successfully",
            "result": result,
            "log_id": log.id
        }
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        
        # Create error log
        log = ProcessingLog(
            file_name=file.filename,
            email_sender="manual_upload",
            processing_status='ERROR',
            error_details=str(e),
            file_size_bytes=len(content) if 'content' in locals() else 0
        )
        db.add(log)
        db.commit()
        
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# CRUD Endpoints

@app.get("/mappings/", response_model=List[CoTMappingResponse])
def get_mappings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get CoT mappings"""
    mappings = db.query(CoTMapping).offset(skip).limit(limit).all()
    return mappings

@app.get("/mappings/{mapping_id}", response_model=CoTMappingResponse)
def get_mapping(mapping_id: int, db: Session = Depends(get_db)):
    """Get specific CoT mapping"""
    mapping = db.query(CoTMapping).filter(CoTMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping

@app.get("/mappings/new-items/")
def get_new_items(db: Session = Depends(get_db)):
    """Get newly identified channels and COTs"""
    new_channels = db.query(CoTMapping).filter(CoTMapping.is_new_channel == True).all()
    new_cots = db.query(CoTMapping).filter(CoTMapping.is_new_cot == True).all()
    
    return {
        "new_channels": [
            {
                "channel": m.new_channel,
                "source_file": m.source_file,
                "processed_date": m.processed_date
            } for m in new_channels
        ],
        "new_cots": [
            {
                "cot": m.new_cot,
                "source_file": m.source_file,
                "processed_date": m.processed_date
            } for m in new_cots
        ]
    }

# Processing Logs

@app.get("/processing-logs/", response_model=List[ProcessingLogResponse])
def get_processing_logs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get processing logs"""
    logs = db.query(ProcessingLog).order_by(
        ProcessingLog.processed_at.desc()
    ).offset(skip).limit(limit).all()
    return logs

@app.get("/processing-logs/{log_id}", response_model=ProcessingLogResponse)
def get_processing_log(log_id: int, db: Session = Depends(get_db)):
    """Get specific processing log"""
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

# Chat Endpoints

@app.post("/chat/", response_model=ChatResponse)
def chat_with_data(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with AI about the data"""
    try:
        answer = chatbot.query_data(request.question, db)
        return ChatResponse(
            question=request.question,
            answer=answer,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/chat/reload-context/")
def reload_chat_context(db: Session = Depends(get_db)):
    """Reload chat context"""
    try:
        count = chatbot.refresh_context(db)
        return {"message": f"Context reloaded with {count} mappings"}
    except Exception as e:
        logger.error(f"Error reloading context: {e}")
        raise HTTPException(status_code=500, detail=f"Error reloading context: {str(e)}")

@app.get("/chat/suggestions/")
def get_chat_suggestions():
    """Get suggested questions"""
    return {"suggestions": chatbot.get_suggested_questions()}

# Email Configuration

@app.get("/email-config/", response_model=EmailConfigResponse)
def get_email_config(db: Session = Depends(get_db)):
    """Get email configuration"""
    config = db.query(EmailConfig).first()
    if not config:
        # Create default config
        config = EmailConfig()
        db.add(config)
        db.commit()
    
    return EmailConfigResponse(
        imap_server=config.imap_server,
        imap_port=config.imap_port,
        email_username=config.email_username,
        smtp_server=config.smtp_server,
        smtp_port=config.smtp_port,
        enabled=config.enabled
    )

@app.put("/email-config/")
def update_email_config(
    imap_server: str,
    imap_port: int,
    email_username: str,
    email_password: str,
    smtp_server: str,
    smtp_port: int,
    db: Session = Depends(get_db)
):
    """Update email configuration"""
    config = db.query(EmailConfig).first()
    if not config:
        config = EmailConfig()
        db.add(config)
    
    config.imap_server = imap_server
    config.imap_port = imap_port
    config.email_username = email_username
    config.email_password = email_password
    config.smtp_server = smtp_server
    config.smtp_port = smtp_port
    config.enabled = True
    config.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Email configuration updated successfully"}

# Email Monitoring

@app.post("/email-monitoring/start/")
def start_email_monitoring():
    """Start email monitoring"""
    try:
        email_processor.start_monitoring()
        return {"message": "Email monitoring started"}
    except Exception as e:
        logger.error(f"Error starting email monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")

@app.post("/email-monitoring/stop/")
def stop_email_monitoring():
    """Stop email monitoring"""
    try:
        email_processor.stop_monitoring()
        return {"message": "Email monitoring stopped"}
    except Exception as e:
        logger.error(f"Error stopping email monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping monitoring: {str(e)}")

@app.get("/email-monitoring/status/")
def get_monitoring_status():
    """Get email monitoring status"""
    return email_processor.get_monitoring_status()

# Analytics

@app.get("/analytics/summary/")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Get analytics summary"""
    try:
        stats = get_db_stats()
        
        # Get recent files
        recent_logs = db.query(ProcessingLog).order_by(
            ProcessingLog.processed_at.desc()
        ).limit(10).all()
        
        return {
            "total_mappings": stats.get("total_mappings", 0),
            "new_channels_identified": stats.get("new_channels", 0),
            "new_cots_identified": stats.get("new_cots", 0),
            "recent_files_processed": len(recent_logs),
            "recent_files": [
                {
                    "file": log.file_name,
                    "processed_at": log.processed_at,
                    "status": log.processing_status,
                    "total_records": log.total_records or 0,
                    "new_items": (log.new_channels_found or 0) + (log.new_cots_found or 0)
                } for log in recent_logs
            ]
        }
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")

@app.get("/analytics/trends/")
def get_trends(days: int = 7, db: Session = Depends(get_db)):
    """Get trend analysis"""
    try:
        trends = chatbot.analyze_trends(db, days)
        return trends
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting trends: {str(e)}")

# System Management

@app.post("/system/backup/")
def create_backup():
    """Create database backup"""
    try:
        backup_path = backup_db()
        return {"message": "Backup created successfully", "backup_path": backup_path}
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating backup: {str(e)}")

@app.post("/system/cleanup-logs/")
def cleanup_logs(days: int = 30, db: Session = Depends(get_db)):
    """Clean up old logs"""
    try:
        deleted_count = cleanup_old_logs(days)
        return {"message": f"Deleted {deleted_count} old log entries"}
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up logs: {str(e)}")

@app.get("/system/stats/")
def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        stats = get_db_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

# Error handlers

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting CoT Mapping System...")
    logger.info(f"Dashboard will be available at: http://localhost:{settings.api_port}/dashboard")
    logger.info(f"API docs will be available at: http://localhost:{settings.api_port}/docs")
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )