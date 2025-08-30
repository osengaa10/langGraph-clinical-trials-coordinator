#!/usr/bin/env python3
"""
Cleanup Service for Clinical Trials Coordinator

This service handles periodic cleanup of abandoned sessions, orphaned resources,
and expired data. It can be run as a standalone script or imported as a module.
"""

import time
import logging
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import json
from session_store import session_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup.log')
    ]
)
logger = logging.getLogger(__name__)

class CleanupService:
    def __init__(self, cleanup_interval_minutes=60):
        self.cleanup_interval = cleanup_interval_minutes * 60  # Convert to seconds
        self.running = False
        
    def start(self):
        """Start the cleanup service"""
        self.running = True
        logger.info("Cleanup service started")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            while self.running:
                self._run_cleanup()
                
                # Wait for next cleanup cycle
                sleep_time = 0
                while sleep_time < self.cleanup_interval and self.running:
                    time.sleep(10)  # Check every 10 seconds if we should stop
                    sleep_time += 10
                    
        except Exception as e:
            logger.error(f"Cleanup service error: {e}")
        finally:
            logger.info("Cleanup service stopped")
    
    def stop(self):
        """Stop the cleanup service"""
        self.running = False
        logger.info("Stopping cleanup service...")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def _run_cleanup(self):
        """Run all cleanup tasks"""
        logger.info("Starting cleanup cycle")
        start_time = time.time()
        
        try:
            # 1. Clean up expired sessions
            self._cleanup_expired_sessions()
            
            # 2. Clean up orphaned resources
            self._cleanup_orphaned_resources()
            
            # 3. Clean up temporary files
            self._cleanup_temp_files()
            
            # 4. Log cleanup statistics
            self._log_cleanup_stats()
            
            elapsed = time.time() - start_time
            logger.info(f"Cleanup cycle completed in {elapsed:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error during cleanup cycle: {e}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions using session store"""
        try:
            active_sessions = session_store.list_active_sessions()
            expired_count = 0
            
            for session_info in active_sessions:
                # Sessions older than 48 hours are considered expired
                if session_info.get('age_hours', 0) > 48:
                    session_id = session_info['session_id']
                    success = session_store.remove_session(session_id)
                    if success:
                        expired_count += 1
                        logger.info(f"Removed expired session: {session_id}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
            else:
                logger.debug("No expired sessions found")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def _cleanup_orphaned_resources(self):
        """Clean up resources that don't have corresponding sessions"""
        try:
            # Get list of active session IDs
            active_sessions = session_store.list_active_sessions()
            active_session_ids = {s['session_id'] for s in active_sessions}
            
            orphaned_count = 0
            
            # Check studies directory
            studies_dir = Path("./studies")
            if studies_dir.exists():
                for session_dir in studies_dir.iterdir():
                    if session_dir.is_dir() and session_dir.name not in active_session_ids:
                        try:
                            shutil.rmtree(session_dir)
                            orphaned_count += 1
                            logger.info(f"Removed orphaned studies directory: {session_dir.name}")
                        except Exception as e:
                            logger.error(f"Error removing studies directory {session_dir}: {e}")
            
            # Check database directory
            db_dir = Path("./db")
            if db_dir.exists():
                for session_dir in db_dir.iterdir():
                    if session_dir.is_dir() and session_dir.name not in active_session_ids:
                        try:
                            shutil.rmtree(session_dir)
                            orphaned_count += 1
                            logger.info(f"Removed orphaned database directory: {session_dir.name}")
                        except Exception as e:
                            logger.error(f"Error removing database directory {session_dir}: {e}")
            
            # Check RAG data directory
            rag_data_dir = Path("./rag_data/data")
            if rag_data_dir.exists():
                for session_dir in rag_data_dir.iterdir():
                    if session_dir.is_dir() and session_dir.name not in active_session_ids:
                        try:
                            shutil.rmtree(session_dir)
                            orphaned_count += 1
                            logger.info(f"Removed orphaned RAG data directory: {session_dir.name}")
                        except Exception as e:
                            logger.error(f"Error removing RAG data directory {session_dir}: {e}")
            
            if orphaned_count > 0:
                logger.info(f"Cleaned up {orphaned_count} orphaned resource directories")
            else:
                logger.debug("No orphaned resources found")
                
        except Exception as e:
            logger.error(f"Error cleaning up orphaned resources: {e}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_count = 0
            
            # Clean up temporary session files
            sessions_dir = Path("./sessions")
            if sessions_dir.exists():
                for temp_file in sessions_dir.glob("*.tmp"):
                    try:
                        # Remove temp files older than 1 hour
                        if time.time() - temp_file.stat().st_mtime > 3600:
                            temp_file.unlink()
                            temp_count += 1
                            logger.info(f"Removed temporary file: {temp_file.name}")
                    except Exception as e:
                        logger.error(f"Error removing temp file {temp_file}: {e}")
            
            # Clean up other temporary files (add more patterns as needed)
            for pattern in ["*.tmp", "*.temp", "*.log.old"]:
                for temp_file in Path(".").glob(pattern):
                    try:
                        if time.time() - temp_file.stat().st_mtime > 3600:
                            temp_file.unlink()
                            temp_count += 1
                            logger.info(f"Removed temporary file: {temp_file.name}")
                    except Exception as e:
                        logger.error(f"Error removing temp file {temp_file}: {e}")
            
            if temp_count > 0:
                logger.info(f"Cleaned up {temp_count} temporary files")
            else:
                logger.debug("No temporary files to clean up")
                
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
    
    def _log_cleanup_stats(self):
        """Log current system statistics"""
        try:
            active_sessions = session_store.list_active_sessions()
            
            # Count resource directories
            studies_count = len(list(Path("./studies").iterdir())) if Path("./studies").exists() else 0
            db_count = len(list(Path("./db").iterdir())) if Path("./db").exists() else 0
            rag_count = len(list(Path("./rag_data/data").iterdir())) if Path("./rag_data/data").exists() else 0
            
            logger.info(f"System stats - Active sessions: {len(active_sessions)}, "
                       f"Studies dirs: {studies_count}, DB dirs: {db_count}, RAG dirs: {rag_count}")
            
            # Log session details
            for session in active_sessions:
                age_hours = session.get('age_hours', 0)
                inactive_hours = session.get('inactive_hours', 0) if 'inactive_hours' in session else age_hours
                logger.debug(f"Session {session['session_id']}: age={age_hours:.1f}h, inactive={inactive_hours:.1f}h")
                
        except Exception as e:
            logger.error(f"Error logging cleanup stats: {e}")
    
    def force_cleanup_all(self):
        """Force cleanup of all sessions and resources - for development/testing"""
        logger.warning("Force cleanup requested - removing ALL sessions and resources")
        
        try:
            # Remove all sessions
            session_store.force_cleanup_all()
            
            # Remove all resource directories
            for dir_path in ["./studies", "./db", "./rag_data/data"]:
                dir_path = Path(dir_path)
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Cleared directory: {dir_path}")
            
            logger.warning("Force cleanup completed - all data cleared")
            
        except Exception as e:
            logger.error(f"Error during force cleanup: {e}")

def main():
    """Main entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clinical Trials Cleanup Service')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Cleanup interval in minutes (default: 60)')
    parser.add_argument('--once', action='store_true', 
                       help='Run cleanup once and exit')
    parser.add_argument('--force', action='store_true', 
                       help='Force cleanup all sessions and resources')
    parser.add_argument('--stats', action='store_true', 
                       help='Show current statistics and exit')
    
    args = parser.parse_args()
    
    cleanup_service = CleanupService(cleanup_interval_minutes=args.interval)
    
    if args.force:
        cleanup_service.force_cleanup_all()
        return
    
    if args.stats:
        cleanup_service._log_cleanup_stats()
        return
    
    if args.once:
        cleanup_service._run_cleanup()
        return
    
    # Run continuous cleanup service
    try:
        cleanup_service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        cleanup_service.stop()

if __name__ == "__main__":
    main()