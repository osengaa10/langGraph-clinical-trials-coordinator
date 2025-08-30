import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import shutil
import threading
import logging

logger = logging.getLogger(__name__)

class SessionStore:
    def __init__(self, sessions_dir="./sessions", cleanup_interval_hours=1):
        self.sessions_dir = Path(sessions_dir)
        self.cleanup_interval = cleanup_interval_hours * 3600  # Convert to seconds
        self.session_timeout = 48 * 3600  # 48 hours in seconds
        
        # Create sessions directory if it doesn't exist
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Start cleanup service
        self._start_cleanup_service()
    
    def _get_session_file(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"
    
    def _get_session_resources_dir(self, session_id: str) -> Path:
        return self.sessions_dir / session_id
    
    def save_session(self, session_id: str, state: Dict[Any, Any]) -> bool:
        try:
            session_file = self._get_session_file(session_id)
            
            # Prepare session data with metadata
            session_data = {
                'session_id': session_id,
                'state': state,
                'created_at': time.time(),
                'last_updated': time.time(),
                'last_activity': time.time()
            }
            
            # Save to temporary file first, then rename for atomic write
            temp_file = session_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            temp_file.rename(session_file)
            logger.info(f"Session {session_id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[Any, Any]]:
        try:
            session_file = self._get_session_file(session_id)
            
            if not session_file.exists():
                logger.info(f"Session {session_id} not found")
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is expired
            if self._is_session_expired(session_data):
                logger.info(f"Session {session_id} expired, removing")
                self.remove_session(session_id)
                return None
            
            # Update last activity
            session_data['last_activity'] = time.time()
            self.save_session(session_id, session_data['state'])
            
            logger.info(f"Session {session_id} loaded successfully")
            return session_data
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, state_updates: Dict[Any, Any]) -> bool:
        try:
            session_data = self.load_session(session_id)
            if not session_data:
                # Create new session if it doesn't exist
                return self.save_session(session_id, state_updates)
            
            # Merge updates with existing state
            session_data['state'].update(state_updates)
            session_data['last_updated'] = time.time()
            
            return self.save_session(session_id, session_data['state'])
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def remove_session(self, session_id: str) -> bool:
        try:
            session_file = self._get_session_file(session_id)
            resources_dir = self._get_session_resources_dir(session_id)
            
            # Remove session file
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Session file {session_id} removed")
            
            # Remove associated resources (studies, embeddings, etc.)
            self._cleanup_session_resources(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing session {session_id}: {e}")
            return False
    
    def list_active_sessions(self) -> list:
        active_sessions = []
        try:
            for session_file in self.sessions_dir.glob("*.json"):
                if session_file.name.endswith('.tmp'):
                    continue
                    
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    if not self._is_session_expired(session_data):
                        active_sessions.append({
                            'session_id': session_data['session_id'],
                            'created_at': session_data['created_at'],
                            'last_activity': session_data['last_activity'],
                            'age_hours': (time.time() - session_data['created_at']) / 3600
                        })
                except Exception as e:
                    logger.error(f"Error reading session file {session_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            
        return active_sessions
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        session_data = self.load_session(session_id)
        if not session_data:
            return None
        
        return {
            'session_id': session_id,
            'created_at': session_data['created_at'],
            'last_activity': session_data['last_activity'],
            'age_hours': (time.time() - session_data['created_at']) / 3600,
            'inactive_hours': (time.time() - session_data['last_activity']) / 3600,
            'state': session_data['state']
        }
    
    def _is_session_expired(self, session_data: Dict[Any, Any]) -> bool:
        last_activity = session_data.get('last_activity', 0)
        return (time.time() - last_activity) > self.session_timeout
    
    def _cleanup_session_resources(self, session_id: str):
        """Clean up associated resources for a session"""
        try:
            # Clean up studies directory
            studies_dir = Path("./studies") / session_id
            if studies_dir.exists():
                shutil.rmtree(studies_dir)
                logger.info(f"Cleaned up studies directory for session {session_id}")
            
            # Clean up database directory
            db_dir = Path("./db") / session_id
            if db_dir.exists():
                shutil.rmtree(db_dir)
                logger.info(f"Cleaned up database directory for session {session_id}")
            
            # Clean up RAG data directory
            rag_dir = Path("./rag_data/data") / session_id
            if rag_dir.exists():
                shutil.rmtree(rag_dir)
                logger.info(f"Cleaned up RAG data directory for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up resources for session {session_id}: {e}")
    
    def _cleanup_expired_sessions(self):
        """Remove all expired sessions and their resources"""
        try:
            expired_count = 0
            for session_file in self.sessions_dir.glob("*.json"):
                if session_file.name.endswith('.tmp'):
                    continue
                    
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    if self._is_session_expired(session_data):
                        session_id = session_data['session_id']
                        self.remove_session(session_id)
                        expired_count += 1
                        logger.info(f"Expired session {session_id} cleaned up")
                        
                except Exception as e:
                    logger.error(f"Error processing session file {session_file}: {e}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
                
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
    
    def _start_cleanup_service(self):
        """Start background cleanup service"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self._cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Error in cleanup service: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Session cleanup service started")
    
    def force_cleanup_all(self):
        """Force cleanup of all sessions - useful for development/testing"""
        try:
            for session_file in self.sessions_dir.glob("*.json"):
                if session_file.name.endswith('.tmp'):
                    continue
                    
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    session_id = session_data['session_id']
                    self.remove_session(session_id)
                    logger.info(f"Force removed session {session_id}")
                    
                except Exception as e:
                    logger.error(f"Error force removing session file {session_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error during force cleanup: {e}")

# Global session store instance
session_store = SessionStore()