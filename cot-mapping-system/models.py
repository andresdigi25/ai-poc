from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Index
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
from typing import Optional

class CoTMapping(Base):
    """Model for Class of Trade mappings"""
    __tablename__ = "cot_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    ic_channel = Column(String(100), index=True, comment="Original IC Channel")
    ic_cot = Column(String(200), index=True, comment="Original IC COT")
    new_channel = Column(String(100), index=True, comment="New Channel mapping")
    new_cot = Column(String(200), index=True, comment="New COT mapping")
    notes = Column(Text, comment="Additional notes or comments")
    source_file = Column(String(255), comment="Source Excel file name")
    processed_date = Column(DateTime, default=datetime.utcnow, comment="When this mapping was processed")
    is_new_channel = Column(Boolean, default=False, index=True, comment="True if this is a new channel")
    is_new_cot = Column(Boolean, default=False, index=True, comment="True if this is a new COT")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Record creation timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Record update timestamp")
    
    # Create composite indexes for better query performance
    __table_args__ = (
        Index('idx_ic_mapping', 'ic_channel', 'ic_cot'),
        Index('idx_new_mapping', 'new_channel', 'new_cot'),
        Index('idx_new_items', 'is_new_channel', 'is_new_cot'),
        Index('idx_processed_date', 'processed_date'),
    )
    
    def __repr__(self):
        return f"<CoTMapping(ic='{self.ic_channel}:{self.ic_cot}' -> new='{self.new_channel}:{self.new_cot}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'ic_channel': self.ic_channel,
            'ic_cot': self.ic_cot,
            'new_channel': self.new_channel,
            'new_cot': self.new_cot,
            'notes': self.notes,
            'source_file': self.source_file,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'is_new_channel': self.is_new_channel,
            'is_new_cot': self.is_new_cot,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProcessingLog(Base):
    """Model for processing logs and audit trail"""
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), index=True, comment="Name of processed file")
    email_sender = Column(String(255), index=True, comment="Email address of sender")
    email_subject = Column(String(500), comment="Email subject line")
    email_message_id = Column(String(255), comment="Email message ID for tracking")
    total_records = Column(Integer, default=0, comment="Total records in file")
    new_channels_found = Column(Integer, default=0, comment="Number of new channels identified")
    new_cots_found = Column(Integer, default=0, comment="Number of new COTs identified")
    records_inserted = Column(Integer, default=0, comment="Number of new records inserted")
    records_updated = Column(Integer, default=0, comment="Number of existing records updated")
    records_skipped = Column(Integer, default=0, comment="Number of records skipped")
    processing_status = Column(String(20), default="PENDING", index=True, comment="Processing status: SUCCESS, ERROR, WARNING")
    error_details = Column(Text, comment="Error details if processing failed")
    processing_time_seconds = Column(Integer, comment="Time taken to process in seconds")
    file_size_bytes = Column(Integer, comment="Size of processed file in bytes")
    new_channels_list = Column(JSON, comment="List of new channels found")
    new_cots_list = Column(JSON, comment="List of new COTs found")
    processed_at = Column(DateTime, default=datetime.utcnow, index=True, comment="When processing completed")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Log entry creation time")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_processing_status', 'processing_status'),
        Index('idx_processed_date', 'processed_at'),
        Index('idx_sender', 'email_sender'),
    )
    
    def __repr__(self):
        return f"<ProcessingLog(file='{self.file_name}', status='{self.processing_status}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'email_sender': self.email_sender,
            'email_subject': self.email_subject,
            'total_records': self.total_records,
            'new_channels_found': self.new_channels_found,
            'new_cots_found': self.new_cots_found,
            'records_inserted': self.records_inserted,
            'records_updated': self.records_updated,
            'processing_status': self.processing_status,
            'error_details': self.error_details,
            'processing_time_seconds': self.processing_time_seconds,
            'new_channels_list': self.new_channels_list,
            'new_cots_list': self.new_cots_list,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EmailConfig(Base):
    """Model for email configuration"""
    __tablename__ = "email_config"
    
    id = Column(Integer, primary_key=True, index=True)
    imap_server = Column(String(255), default="imap.gmail.com", comment="IMAP server address")
    imap_port = Column(Integer, default=993, comment="IMAP server port")
    email_username = Column(String(255), comment="Email username/address")
    email_password = Column(String(255), comment="Email password or app password")
    smtp_server = Column(String(255), default="smtp.gmail.com", comment="SMTP server address")
    smtp_port = Column(Integer, default=587, comment="SMTP server port")
    enabled = Column(Boolean, default=False, comment="Whether email monitoring is enabled")
    email_folder = Column(String(50), default="INBOX", comment="Email folder to monitor")
    search_subject = Column(String(255), default="CoT", comment="Subject filter for emails")
    check_interval = Column(Integer, default=300, comment="Check interval in seconds")
    last_check = Column(DateTime, comment="Last time emails were checked")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Configuration creation time")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last configuration update")
    
    def __repr__(self):
        return f"<EmailConfig(username='{self.email_username}', enabled={self.enabled})>"
    
    def to_dict(self):
        """Convert model to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'imap_server': self.imap_server,
            'imap_port': self.imap_port,
            'email_username': self.email_username,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'enabled': self.enabled,
            'email_folder': self.email_folder,
            'search_subject': self.search_subject,
            'check_interval': self.check_interval,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SystemSettings(Base):
    """Model for system-wide settings"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, index=True, comment="Setting key name")
    setting_value = Column(Text, comment="Setting value (JSON or text)")
    setting_type = Column(String(20), default="string", comment="Setting type: string, integer, boolean, json")
    description = Column(Text, comment="Setting description")
    is_sensitive = Column(Boolean, default=False, comment="Whether this setting contains sensitive data")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Setting creation time")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last setting update")
    
    def __repr__(self):
        return f"<SystemSettings(key='{self.setting_key}', type='{self.setting_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value if not self.is_sensitive else "***",
            'setting_type': self.setting_type,
            'description': self.description,
            'is_sensitive': self.is_sensitive,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLog(Base):
    """Model for audit logging"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), index=True, comment="Action performed: CREATE, UPDATE, DELETE, LOGIN, etc.")
    entity_type = Column(String(50), index=True, comment="Type of entity affected")
    entity_id = Column(Integer, comment="ID of affected entity")
    user_identifier = Column(String(255), comment="User or system that performed action")
    old_values = Column(JSON, comment="Previous values before change")
    new_values = Column(JSON, comment="New values after change")
    ip_address = Column(String(45), comment="IP address of requestor")
    user_agent = Column(String(500), comment="User agent string")
    session_id = Column(String(255), comment="Session identifier")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="When action was performed")
    
    # Indexes for audit queries
    __table_args__ = (
        Index('idx_audit_action', 'action'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_date', 'created_at'),
        Index('idx_audit_user', 'user_identifier'),
    )
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'user_identifier': self.user_identifier,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }