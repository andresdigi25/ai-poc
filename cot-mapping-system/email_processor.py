import imaplib
import email
import smtplib
import schedule
import time
import threading
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging
from sqlalchemy.orm import Session

from database import SessionLocal
from models import EmailConfig, ProcessingLog, CoTMapping
from chat_handler import CoTChatbot
from config import settings

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Handles email monitoring and processing"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.chatbot = CoTChatbot()
        
    def get_email_config(self, db: Session) -> Optional[EmailConfig]:
        """Get active email configuration"""
        config = db.query(EmailConfig).filter(EmailConfig.enabled == True).first()
        if not config:
            logger.warning("No enabled email configuration found")
        return config
    
    def test_imap_connection(self, config: EmailConfig) -> bool:
        """Test IMAP connection"""
        try:
            mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            mail.login(config.email_username, config.email_password)
            mail.select(config.email_folder)
            mail.close()
            mail.logout()
            logger.info("IMAP connection test successful")
            return True
        except Exception as e:
            logger.error(f"IMAP connection test failed: {e}")
            return False
    
    def test_smtp_connection(self, config: EmailConfig) -> bool:
        """Test SMTP connection"""
        try:
            server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            server.starttls()
            server.login(config.email_username, config.email_password)
            server.quit()
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def check_new_emails(self, db: Session) -> List[Dict[str, Any]]:
        """Check for new emails with Excel attachments"""
        config = self.get_email_config(db)
        if not config:
            return []
        
        new_emails = []
        
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            mail.login(config.email_username, config.email_password)
            mail.select(config.email_folder)
            
            # Search for unread emails
            search_criteria = 'UNSEEN'
            if config.search_subject:
                search_criteria += f' SUBJECT "{config.search_subject}"'
            
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return []
            
            message_ids = messages[0].split()
            logger.info(f"Found {len(message_ids)} unread emails")
            
            for msg_id in message_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract email info
                    email_info = {
                        'message_id': email_message.get('Message-ID', ''),
                        'sender': email_message.get('From', ''),
                        'subject': email_message.get('Subject', ''),
                        'date': email_message.get('Date', ''),
                        'attachments': []
                    }
                    
                    # Check for Excel attachments
                    for part in email_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            filename = part.get_filename()
                            if filename and self._is_excel_file(filename):
                                attachment_data = part.get_payload(decode=True)
                                email_info['attachments'].append({
                                    'filename': filename,
                                    'data': attachment_data,
                                    'size': len(attachment_data)
                                })
                    
                    # Only process emails with Excel attachments
                    if email_info['attachments']:
                        new_emails.append(email_info)
                        logger.info(f"Found email with Excel attachment: {email_info['subject']}")
                    
                    # Mark as read
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    logger.error(f"Error processing email {msg_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
            # Update last check time
            config.last_check = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
        
        return new_emails
    
    def _is_excel_file(self, filename: str) -> bool:
        """Check if filename is an Excel file"""
        return filename.lower().endswith(('.xlsx', '.xls'))
    
    def process_excel_attachment(self, attachment_data: bytes, filename: str, 
                                sender: str, subject: str, message_id: str, 
                                db: Session) -> Dict[str, Any]:
        """Process Excel attachment and return results"""
        start_time = datetime.utcnow()
        
        try:
            # Read Excel data
            df = pd.read_excel(BytesIO(attachment_data))
            
            # Process the data using existing logic
            result = self._process_cot_data(df, filename, db)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create processing log
            log = ProcessingLog(
                file_name=filename,
                email_sender=sender,
                email_subject=subject,
                email_message_id=message_id,
                total_records=result.get('total_records', 0),
                new_channels_found=result.get('new_channels_found', 0),
                new_cots_found=result.get('new_cots_found', 0),
                records_inserted=result.get('records_inserted', 0),
                records_updated=result.get('records_updated', 0),
                processing_status='SUCCESS',
                processing_time_seconds=int(processing_time),
                file_size_bytes=len(attachment_data),
                new_channels_list=result.get('new_channels', []),
                new_cots_list=result.get('new_cots', [])
            )
            db.add(log)
            db.commit()
            
            logger.info(f"Successfully processed {filename} from {sender}")
            
            # Send confirmation email
            self._send_confirmation_email(sender, result, filename, db)
            
            return result
            
        except Exception as e:
            # Calculate processing time even for errors
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create error log
            log = ProcessingLog(
                file_name=filename,
                email_sender=sender,
                email_subject=subject,
                email_message_id=message_id,
                processing_status='ERROR',
                error_details=str(e),
                processing_time_seconds=int(processing_time),
                file_size_bytes=len(attachment_data)
            )
            db.add(log)
            db.commit()
            
            logger.error(f"Error processing {filename} from {sender}: {e}")
            
            # Send error notification
            self._send_error_email(sender, str(e), filename, db)
            
            raise
    
    def _process_cot_data(self, df: pd.DataFrame, source_file: str, db: Session) -> Dict[str, Any]:
        """Process CoT mapping data from DataFrame"""
        
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
        
        # Identify new items
        new_items = self._identify_new_items(df, db)
        
        records_inserted = 0
        records_updated = 0
        
        for _, row in df.iterrows():
            try:
                # Check if mapping already exists
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
                continue
        
        db.commit()
        
        return {
            'total_records': len(df),
            'records_inserted': records_inserted,
            'records_updated': records_updated,
            'new_channels_found': len(new_items['new_channels']),
            'new_cots_found': len(new_items['new_cots']),
            'new_channels': new_items['new_channels'],
            'new_cots': new_items['new_cots']
        }
    
    def _identify_new_items(self, df: pd.DataFrame, db: Session) -> Dict[str, List[str]]:
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
        
        return {
            'new_channels': new_channels,
            'new_cots': new_cots
        }
    
    def _send_confirmation_email(self, recipient: str, result: Dict[str, Any], 
                                filename: str, db: Session):
        """Send confirmation email"""
        config = self.get_email_config(db)
        if not config:
            return
        
        try:
            # Generate AI analysis
            ai_analysis = self._generate_ai_analysis(result, filename)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = config.email_username
            msg['To'] = recipient
            msg['Subject'] = f"✅ CoT Processing Completed: {filename}"
            
            # HTML content
            html_content = self._create_success_email_html(result, filename, ai_analysis)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            server.starttls()
            server.login(config.email_username, config.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Confirmation email sent to {recipient}")
            
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
    
    def _send_error_email(self, recipient: str, error: str, filename: str, db: Session):
        """Send error notification email"""
        config = self.get_email_config(db)
        if not config:
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = config.email_username
            msg['To'] = recipient
            msg['Subject'] = f"❌ CoT Processing Error: {filename}"
            
            html_content = self._create_error_email_html(error, filename)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            server.starttls()
            server.login(config.email_username, config.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Error email sent to {recipient}")
            
        except Exception as e:
            logger.error(f"Error sending error email: {e}")
    
    def _generate_ai_analysis(self, result: Dict[str, Any], filename: str) -> str:
        """Generate AI analysis of processing results"""
        try:
            question = f"Analiza los resultados del procesamiento del archivo '{filename}': {result}"
            db = SessionLocal()
            try:
                analysis = self.chatbot.query_data(question, db)
                return analysis
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            return "AI analysis not available"
    
    def _create_success_email_html(self, result: Dict[str, Any], filename: str, ai_analysis: str) -> str:
        """Create HTML content for success email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #27ae60; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .stats {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
                .footer {{ background: #34495e; color: white; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; }}
                .success {{ color: #27ae60; font-weight: bold; }}
                .highlight {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✅ CoT Processing Completed Successfully</h2>
                </div>
                
                <div class="content">
                    <h3>📁 File Information</h3>
                    <div class="stats">
                        <strong>File:</strong> {filename}<br>
                        <strong>Processed on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    </div>
                    
                    <h3>📊 Processing Results</h3>
                    <div class="stats">
                        <ul>
                            <li><strong>Total records:</strong> <span class="success">{result.get('total_records', 0)}</span></li>
                            <li><strong>Records inserted:</strong> <span class="success">{result.get('records_inserted', 0)}</span></li>
                            <li><strong>Records updated:</strong> <span class="success">{result.get('records_updated', 0)}</span></li>
                            <li><strong>New Channels found:</strong> <span class="success">{result.get('new_channels_found', 0)}</span></li>
                            <li><strong>New COTs found:</strong> <span class="success">{result.get('new_cots_found', 0)}</span></li>
                        </ul>
                    </div>
                    
                    <h3>🤖 AI Analysis</h3>
                    <div class="highlight">
                        {ai_analysis}
                    </div>
                    
                    <h3>🆕 New Elements Identified</h3>
                    <div class="stats">
                        <p><strong>New Channels:</strong></p>
                        <ul>
                            {' '.join([f'<li>{channel}</li>' for channel in result.get('new_channels', [])])}
                        </ul>
                        
                        <p><strong>New COTs:</strong></p>
                        <ul>
                            {' '.join([f'<li>{cot}</li>' for cot in result.get('new_cots', [])])}
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Automated message from CoT Mapping System</p>
                    <p>Dashboard: <a href="http://localhost:8000/dashboard" style="color: #3498db;">http://localhost:8000/dashboard</a></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_error_email_html(self, error: str, filename: str) -> str:
        """Create HTML content for error email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #e74c3c; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 15px; margin: 15px 0; border-radius: 5px; border: 1px solid #f5c6cb; }}
                .solutions {{ background: #cce5ff; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ background: #34495e; color: white; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>❌ CoT Processing Error</h2>
                </div>
                
                <div class="content">
                    <h3>📁 File Information</h3>
                    <p><strong>File:</strong> {filename}</p>
                    <p><strong>Attempted on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <h3>⚠️ Error Details</h3>
                    <div class="error">
                        <strong>Error:</strong> {error}
                    </div>
                    
                    <h3>🔧 Possible Solutions</h3>
                    <div class="solutions">
                        <ul>
                            <li>Verify that the Excel file has the correct columns (IC Channel, IC COT, New Channel, New COT)</li>
                            <li>Ensure data format is valid (no special characters in critical fields)</li>
                            <li>Check that the file is not corrupted</li>
                            <li>Try uploading manually through the dashboard</li>
                            <li>Contact the system administrator if the problem persists</li>
                        </ul>
                    </div>
                    
                    <p><strong>Next Steps:</strong> Please review the file and try sending it again. If the issue continues, contact technical support.</p>
                </div>
                
                <div class="footer">
                    <p>Automated message from CoT Mapping System</p>
                    <p>Dashboard: <a href="http://localhost:8000/dashboard" style="color: #3498db;">http://localhost:8000/dashboard</a></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def start_monitoring(self):
        """Start email monitoring in background thread"""
        if self.is_running:
            logger.warning("Email monitoring is already running")
            return
        
        self.is_running = True
        
        def monitor_emails():
            """Background email monitoring function"""
            logger.info("Starting email monitoring...")
            
            while self.is_running:
                try:
                    db = SessionLocal()
                    try:
                        config = self.get_email_config(db)
                        if config and config.enabled:
                            # Check for new emails
                            new_emails = self.check_new_emails(db)
                            
                            # Process each email
                            for email_info in new_emails:
                                for attachment in email_info['attachments']:
                                    try:
                                        self.process_excel_attachment(
                                            attachment['data'],
                                            attachment['filename'],
                                            email_info['sender'],
                                            email_info['subject'],
                                            email_info['message_id'],
                                            db
                                        )
                                    except Exception as e:
                                        logger.error(f"Error processing attachment {attachment['filename']}: {e}")
                        else:
                            logger.debug("Email monitoring disabled or not configured")
                            
                    finally:
                        db.close()
                    
                    # Wait for check interval
                    time.sleep(config.check_interval if config else settings.email_check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in email monitoring loop: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=monitor_emails, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Email monitoring started")
    
    def stop_monitoring(self):
        """Stop email monitoring"""
        if not self.is_running:
            logger.warning("Email monitoring is not running")
            return
        
        self.is_running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        logger.info("Email monitoring stopped")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False,
            'last_check': None  # Would need to track this separately
        }

# Global email processor instance
email_processor = EmailProcessor()