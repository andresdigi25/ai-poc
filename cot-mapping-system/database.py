from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.api_debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Metadata for database operations
metadata = MetaData()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        # Import models to register them
        from models import CoTMapping, ProcessingLog, EmailConfig
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        
        # Create default email config if not exists
        db = SessionLocal()
        try:
            existing_config = db.query(EmailConfig).first()
            if not existing_config:
                default_config = EmailConfig(
                    imap_server=settings.email_imap_server,
                    imap_port=settings.email_imap_port,
                    email_username=settings.email_username,
                    email_password=settings.email_password,
                    smtp_server=settings.email_smtp_server,
                    smtp_port=settings.email_smtp_port,
                    enabled=False  # Disabled until configured
                )
                db.add(default_config)
                db.commit()
                logger.info("Default email configuration created")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def reset_db():
    """Reset database (drop and recreate all tables)"""
    try:
        # Import models
        from models import CoTMapping, ProcessingLog, EmailConfig
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database reset successfully")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

def backup_db(backup_path: str = None):
    """Backup database to file"""
    import shutil
    import os
    from datetime import datetime
    
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{settings.backup_dir}/cot_mappings_backup_{timestamp}.db"
    
    try:
        if "sqlite" in settings.database_url:
            # For SQLite, simply copy the file
            db_file = settings.database_url.replace("sqlite:///", "")
            if os.path.exists(db_file):
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(db_file, backup_path)
                logger.info(f"Database backed up to: {backup_path}")
                return backup_path
            else:
                raise FileNotFoundError(f"Database file not found: {db_file}")
        else:
            # For other databases, would need pg_dump, mysqldump, etc.
            raise NotImplementedError("Backup for non-SQLite databases not implemented")
            
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        raise

def restore_db(backup_path: str):
    """Restore database from backup"""
    import shutil
    import os
    
    try:
        if "sqlite" in settings.database_url:
            db_file = settings.database_url.replace("sqlite:///", "")
            
            if os.path.exists(backup_path):
                # Backup current database first
                current_backup = f"{db_file}.bak"
                if os.path.exists(db_file):
                    shutil.copy2(db_file, current_backup)
                
                # Restore from backup
                shutil.copy2(backup_path, db_file)
                logger.info(f"Database restored from: {backup_path}")
                
                # Verify restoration
                init_db()
                
            else:
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
        else:
            raise NotImplementedError("Restore for non-SQLite databases not implemented")
            
    except Exception as e:
        logger.error(f"Error restoring database: {e}")
        raise

def get_db_stats():
    """Get database statistics"""
    try:
        from models import CoTMapping, ProcessingLog
        
        db = SessionLocal()
        try:
            stats = {
                "total_mappings": db.query(CoTMapping).count(),
                "new_channels": db.query(CoTMapping).filter(CoTMapping.is_new_channel == True).count(),
                "new_cots": db.query(CoTMapping).filter(CoTMapping.is_new_cot == True).count(),
                "total_logs": db.query(ProcessingLog).count(),
                "successful_logs": db.query(ProcessingLog).filter(ProcessingLog.processing_status == "SUCCESS").count(),
                "error_logs": db.query(ProcessingLog).filter(ProcessingLog.processing_status == "ERROR").count()
            }
            return stats
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}

def cleanup_old_logs(days: int = 30):
    """Clean up old processing logs"""
    try:
        from models import ProcessingLog
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        db = SessionLocal()
        try:
            deleted_count = db.query(ProcessingLog).filter(
                ProcessingLog.processed_at < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old log entries")
            return deleted_count
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {e}")
        raise