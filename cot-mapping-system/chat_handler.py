import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

try:
    import ollama
except ImportError:
    logging.warning("Ollama not installed. Chat functionality will be limited.")
    ollama = None

from models import CoTMapping, ProcessingLog, EmailConfig
from config import settings

logger = logging.getLogger(__name__)

class CoTChatbot:
    """Chatbot for querying CoT mapping data using AI"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.ollama_model
        self.context_cache = {}
        self.cache_expiry = timedelta(minutes=15)
        self.last_cache_update = None
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        if not ollama:
            return False
        
        try:
            # Try to list models to check if Ollama is running
            models = ollama.list()
            available_models = [model['name'] for model in models.get('models', [])]
            
            if self.model_name not in available_models:
                logger.warning(f"Model {self.model_name} not found. Available: {available_models}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ollama not available: {e}")
            return False
    
    def _get_context_data(self, db: Session, force_refresh: bool = False) -> Dict[str, Any]:
        """Get and cache context data for AI queries"""
        
        # Check cache validity
        if (not force_refresh and self.last_cache_update and 
            datetime.now() - self.last_cache_update < self.cache_expiry and
            self.context_cache):
            return self.context_cache
        
        try:
            # Get summary statistics
            total_mappings = db.query(CoTMapping).count()
            new_channels_count = db.query(CoTMapping).filter(CoTMapping.is_new_channel == True).count()
            new_cots_count = db.query(CoTMapping).filter(CoTMapping.is_new_cot == True).count()
            
            # Get unique channels and COTs
            unique_channels = [
                row[0] for row in db.query(CoTMapping.new_channel).distinct().all()
                if row[0] is not None
            ]
            unique_cots = [
                row[0] for row in db.query(CoTMapping.new_cot).distinct().all()
                if row[0] is not None
            ]
            
            # Get recent processing logs
            recent_logs = db.query(ProcessingLog).order_by(
                desc(ProcessingLog.processed_at)
            ).limit(10).all()
            
            # Get today's statistics
            today = datetime.now().date()
            today_logs = db.query(ProcessingLog).filter(
                func.date(ProcessingLog.processed_at) == today
            ).all()
            
            # Get weekly statistics
            week_ago = datetime.now() - timedelta(days=7)
            weekly_logs = db.query(ProcessingLog).filter(
                ProcessingLog.processed_at >= week_ago
            ).all()
            
            # Get error statistics
            error_logs = db.query(ProcessingLog).filter(
                ProcessingLog.processing_status == 'ERROR'
            ).order_by(desc(ProcessingLog.processed_at)).limit(5).all()
            
            # Get most recent successful processing
            last_success = db.query(ProcessingLog).filter(
                ProcessingLog.processing_status == 'SUCCESS'
            ).order_by(desc(ProcessingLog.processed_at)).first()
            
            # Get distribution by channel
            channel_distribution = db.query(
                CoTMapping.new_channel, 
                func.count(CoTMapping.id).label('count')
            ).group_by(CoTMapping.new_channel).all()
            
            # Build context
            context = {
                "summary": {
                    "total_mappings": total_mappings,
                    "new_channels_identified": new_channels_count,
                    "new_cots_identified": new_cots_count,
                    "unique_channels_count": len(unique_channels),
                    "unique_cots_count": len(unique_cots)
                },
                "channels": unique_channels[:50],  # Limit for context size
                "cots": unique_cots[:50],  # Limit for context size
                "today_stats": {
                    "files_processed": len(today_logs),
                    "total_records": sum(log.total_records or 0 for log in today_logs),
                    "new_items_found": sum((log.new_channels_found or 0) + (log.new_cots_found or 0) for log in today_logs),
                    "successful_files": len([log for log in today_logs if log.processing_status == 'SUCCESS']),
                    "failed_files": len([log for log in today_logs if log.processing_status == 'ERROR'])
                },
                "weekly_stats": {
                    "files_processed": len(weekly_logs),
                    "total_records": sum(log.total_records or 0 for log in weekly_logs),
                    "new_items_found": sum((log.new_channels_found or 0) + (log.new_cots_found or 0) for log in weekly_logs),
                    "successful_files": len([log for log in weekly_logs if log.processing_status == 'SUCCESS']),
                    "failed_files": len([log for log in weekly_logs if log.processing_status == 'ERROR'])
                },
                "recent_files": [
                    {
                        "filename": log.file_name,
                        "sender": log.email_sender,
                        "processed_at": log.processed_at.isoformat() if log.processed_at else None,
                        "status": log.processing_status,
                        "total_records": log.total_records or 0,
                        "new_channels": log.new_channels_found or 0,
                        "new_cots": log.new_cots_found or 0,
                        "processing_time": log.processing_time_seconds
                    } for log in recent_logs
                ],
                "recent_errors": [
                    {
                        "filename": log.file_name,
                        "error": log.error_details,
                        "processed_at": log.processed_at.isoformat() if log.processed_at else None
                    } for log in error_logs
                ],
                "last_successful_processing": {
                    "filename": last_success.file_name if last_success else None,
                    "processed_at": last_success.processed_at.isoformat() if last_success and last_success.processed_at else None,
                    "records": last_success.total_records if last_success else 0,
                    "new_items": (last_success.new_channels_found or 0) + (last_success.new_cots_found or 0) if last_success else 0
                } if last_success else None,
                "channel_distribution": [
                    {"channel": ch[0], "count": ch[1]} for ch in channel_distribution
                ]
            }
            
            # Cache the context
            self.context_cache = context
            self.last_cache_update = datetime.now()
            
            logger.info(f"Context updated with {total_mappings} mappings and {len(recent_logs)} recent logs")
            
            return context
            
        except Exception as e:
            logger.error(f"Error building context data: {e}")
            return {}
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """Create system prompt with context data"""
        
        prompt = f"""You are an AI assistant specialized in analyzing Class of Trades (CoT) mapping data.

Current System Data:
- Total CoT mappings: {context['summary']['total_mappings']}
- New channels identified: {context['summary']['new_channels_identified']}
- New COTs identified: {context['summary']['new_cots_identified']}
- Unique channels: {context['summary']['unique_channels_count']}
- Unique COTs: {context['summary']['unique_cots_count']}

Today's Activity:
- Files processed: {context['today_stats']['files_processed']}
- Records processed: {context['today_stats']['total_records']}
- New items found: {context['today_stats']['new_items_found']}
- Success rate: {context['today_stats']['successful_files']}/{context['today_stats']['files_processed']} files

Weekly Activity:
- Files processed: {context['weekly_stats']['files_processed']}
- Records processed: {context['weekly_stats']['total_records']}
- New items found: {context['weekly_stats']['new_items_found']}

Recent Files: {json.dumps(context['recent_files'][:3], indent=2)}

Recent Errors: {json.dumps(context['recent_errors'], indent=2)}

Available Channels (sample): {', '.join(context['channels'][:20])}
Available COTs (sample): {', '.join(context['cots'][:20])}

You should:
1. Answer questions about CoT mapping data accurately
2. Provide specific numbers when asked about statistics
3. Analyze trends when asked about patterns
4. Suggest improvements when appropriate
5. Be concise but informative
6. Use the actual data provided above

When answering:
- Use specific numbers from the data
- Reference actual file names and dates when relevant
- Provide actionable insights
- Be conversational but professional
"""
        
        return prompt
    
    def query_data(self, question: str, db: Session, force_refresh: bool = False) -> str:
        """Process user question and return AI response"""
        
        # Check if Ollama is available
        if not self._check_ollama_availability():
            return self._fallback_response(question, db)
        
        try:
            # Get context data
            context = self._get_context_data(db, force_refresh)
            
            if not context:
                return "I'm having trouble accessing the data right now. Please try again later."
            
            # Create system prompt
            system_prompt = self._create_system_prompt(context)
            
            # Create messages for Ollama
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": question
                }
            ]
            
            # Query Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error querying AI: {e}")
            return self._fallback_response(question, db)
    
    def _fallback_response(self, question: str, db: Session) -> str:
        """Provide fallback response when AI is not available"""
        
        try:
            context = self._get_context_data(db)
            
            # Simple keyword-based responses
            question_lower = question.lower()
            
            if any(word in question_lower for word in ['total', 'count', 'how many']):
                if 'mapping' in question_lower:
                    return f"Total mappings in system: {context['summary']['total_mappings']}"
                elif 'channel' in question_lower:
                    return f"New channels identified: {context['summary']['new_channels_identified']}, Total unique channels: {context['summary']['unique_channels_count']}"
                elif 'cot' in question_lower:
                    return f"New COTs identified: {context['summary']['new_cots_identified']}, Total unique COTs: {context['summary']['unique_cots_count']}"
            
            elif any(word in question_lower for word in ['today', 'recent', 'latest']):
                return f"Today's activity: {context['today_stats']['files_processed']} files processed, {context['today_stats']['total_records']} records, {context['today_stats']['new_items_found']} new items found"
            
            elif any(word in question_lower for word in ['error', 'problem', 'failed']):
                return f"Recent errors: {context['today_stats']['failed_files']} failed files today, {context['weekly_stats']['failed_files']} failed files this week"
            
            elif any(word in question_lower for word in ['last', 'previous']):
                if context['last_successful_processing']:
                    last = context['last_successful_processing']
                    return f"Last successful processing: {last['filename']} with {last['records']} records and {last['new_items']} new items"
                else:
                    return "No recent successful processing found"
            
            else:
                return f"I can tell you that we have {context['summary']['total_mappings']} total mappings with {context['summary']['new_channels_identified']} new channels and {context['summary']['new_cots_identified']} new COTs identified. AI analysis is currently unavailable."
                
        except Exception as e:
            logger.error(f"Error in fallback response: {e}")
            return "I'm having trouble accessing the data. Please check the system status."
    
    def refresh_context(self, db: Session) -> int:
        """Manually refresh context cache"""
        self._get_context_data(db, force_refresh=True)
        return self.context_cache.get('summary', {}).get('total_mappings', 0)
    
    def get_suggested_questions(self) -> List[str]:
        """Get list of suggested questions for users"""
        return [
            "¿Cuántos registros nuevos llegaron hoy?",
            "¿Cuáles son los nuevos channels identificados?",
            "¿Cuántos COTs nuevos se encontraron esta semana?",
            "Muéstrame un resumen del último archivo procesado",
            "¿Hay errores en los procesamientos recientes?",
            "¿Cuál es la distribución por channels?",
            "¿Cuántos archivos se procesaron exitosamente hoy?",
            "¿Qué archivos tuvieron errores recientemente?",
            "Dame estadísticas de la semana pasada",
            "¿Cuál fue el último procesamiento exitoso?"
        ]
    
    def analyze_trends(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """Analyze trends over specified period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            logs = db.query(ProcessingLog).filter(
                ProcessingLog.processed_at >= cutoff_date
            ).order_by(ProcessingLog.processed_at).all()
            
            if not logs:
                return {"message": f"No data available for the last {days} days"}
            
            # Group by day
            daily_stats = {}
            for log in logs:
                day = log.processed_at.date()
                if day not in daily_stats:
                    daily_stats[day] = {
                        'files': 0,
                        'records': 0,
                        'new_items': 0,
                        'successes': 0,
                        'errors': 0
                    }
                
                daily_stats[day]['files'] += 1
                daily_stats[day]['records'] += log.total_records or 0
                daily_stats[day]['new_items'] += (log.new_channels_found or 0) + (log.new_cots_found or 0)
                
                if log.processing_status == 'SUCCESS':
                    daily_stats[day]['successes'] += 1
                elif log.processing_status == 'ERROR':
                    daily_stats[day]['errors'] += 1
            
            return {
                "period_days": days,
                "total_files": len(logs),
                "daily_breakdown": daily_stats,
                "average_files_per_day": len(logs) / days,
                "success_rate": sum(1 for log in logs if log.processing_status == 'SUCCESS') / len(logs) * 100
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"error": str(e)}