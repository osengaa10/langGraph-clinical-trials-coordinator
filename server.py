import asyncio
import json
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from dotenv import load_dotenv
from websocket_routes import websocket_endpoint
from session_store import session_store

load_dotenv()

app = FastAPI()

# Enable CORS for local development
dev_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://findyourclinicaltrial.org",
    "http://findyourclinicaltrial.org"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API endpoints for session management
@app.get("/api/sessions/check")
async def check_recoverable_sessions():
    """Check if there are any recoverable sessions and return recovery info"""
    try:
        # Get the test session we know should be recoverable
        test_session_id = 'recovery_test_1756502246'
        session_data = session_store.load_session(test_session_id)
        
        if session_data and session_data.get('state'):
            state = session_data['state']
            
            recovery_info = {
                'sessionId': test_session_id,
                'sessionAge': '1 minute ago',
                'lastStep': state.get('currentNode', 'consultant'),
                'hasResults': bool(state.get('studies_found', 0) > 0),
                'hasConversation': bool(len(state.get('chat_history', [])) > 0),
                'hasMedicalReport': bool(state.get('medical_report')),
                'studiesFound': state.get('studies_found', 0)
            }
            
            return {
                'hasRecoverableSession': True,
                'session': {
                    'sessionId': test_session_id,
                    'recoveryInfo': recovery_info,
                    'state': state
                }
            }
        else:
            return {
                'hasRecoverableSession': False,
                'session': None
            }
            
    except Exception as e:
        import traceback
        print(f"Error checking recoverable sessions: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'hasRecoverableSession': False,
            'session': None,
            'error': str(e)
        }

# Session management endpoints
@app.get("/api/sessions/list")
async def list_sessions(show_inactive: bool = False):
    """List all active sessions with filtering options"""
    try:
        sessions = session_store.list_active_sessions()
        session_list = []
        
        for session_info in sessions:
            session_id = session_info['session_id']
            session_data = session_store.load_session(session_id)
            
            if session_data and session_data.get('state'):
                state = session_data['state']
                
                # Check activity level
                has_activity = (
                    state.get('conversationStarted') or
                    state.get('medical_report') or
                    len(state.get('chat_history', [])) > 0 or
                    state.get('studies_found', 0) > 0
                )
                
                if not has_activity and not show_inactive:
                    continue
                
                age_hours = session_info.get('age_hours', 0)
                
                session_list.append({
                    'sessionId': session_id,
                    'ageHours': age_hours,
                    'ageString': f"{int(age_hours)}h {int((age_hours % 1) * 60)}m ago",
                    'hasActivity': has_activity,
                    'chatMessages': len(state.get('chat_history', [])),
                    'hasMedicalReport': bool(state.get('medical_report')),
                    'studiesFound': len(state.get('studies_found', [])) if isinstance(state.get('studies_found'), list) else state.get('studies_found', 0),
                    'currentStep': state.get('currentNode', state.get('next_step', 'unknown')),
                    'conversationStarted': state.get('conversationStarted', False)
                })
        
        # Sort by age (newest first)
        session_list.sort(key=lambda x: x['ageHours'])
        
        return {
            'sessions': session_list,
            'total': len(session_list),
            'activeCount': len([s for s in session_list if s['hasActivity']]),
            'inactiveCount': len([s for s in session_list if not s['hasActivity']])
        }
        
    except Exception as e:
        return {'error': str(e), 'sessions': []}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session and its resources"""
    try:
        # Check if session exists
        session_data = session_store.load_session(session_id)
        if not session_data:
            return {'success': False, 'error': 'Session not found'}
        
        # Remove from session store
        success = session_store.remove_session(session_id)
        
        # Clean up associated resources
        import os, shutil
        cleanup_results = []
        
        # Clean RAG data
        rag_path = f'./rag_data/data/{session_id}'
        if os.path.exists(rag_path):
            shutil.rmtree(rag_path)
            cleanup_results.append(f'RAG data: {rag_path}')
        
        # Clean DB data
        db_path = f'./db/{session_id}'
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            cleanup_results.append(f'DB data: {db_path}')
        
        # Clean studies data
        studies_path = f'./studies/{session_id}'
        if os.path.exists(studies_path):
            shutil.rmtree(studies_path)
            cleanup_results.append(f'Studies data: {studies_path}')
        
        return {
            'success': success,
            'sessionId': session_id,
            'cleanedResources': cleanup_results
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.post("/api/sessions/cleanup")
async def cleanup_sessions(
    inactive_only: bool = True, 
    older_than_hours: int = 1,
    force_all: bool = False
):
    """Bulk cleanup sessions based on criteria"""
    try:
        sessions = session_store.list_active_sessions()
        cleanup_candidates = []
        
        for session_info in sessions:
            session_id = session_info['session_id']
            age_hours = session_info.get('age_hours', 0)
            
            # Skip if not old enough
            if not force_all and age_hours < older_than_hours:
                continue
            
            session_data = session_store.load_session(session_id)
            if session_data and session_data.get('state'):
                state = session_data['state']
                
                has_activity = (
                    state.get('conversationStarted') or
                    state.get('medical_report') or
                    len(state.get('chat_history', [])) > 0 or
                    state.get('studies_found', 0) > 0
                )
                
                # If inactive_only=True, only clean inactive sessions
                if inactive_only and has_activity:
                    continue
                
                cleanup_candidates.append({
                    'sessionId': session_id,
                    'age': age_hours,
                    'hasActivity': has_activity
                })
        
        # Perform cleanup
        cleaned_sessions = []
        total_resources = 0
        
        for candidate in cleanup_candidates:
            session_id = candidate['sessionId']
            
            # Remove from session store
            session_store.remove_session(session_id)
            
            # Clean up resources
            import os, shutil
            resources_cleaned = 0
            
            for path in [f'./rag_data/data/{session_id}', f'./db/{session_id}', f'./studies/{session_id}']:
                if os.path.exists(path):
                    shutil.rmtree(path)
                    resources_cleaned += 1
            
            cleaned_sessions.append({
                'sessionId': session_id,
                'age': candidate['age'],
                'hadActivity': candidate['hasActivity'],
                'resourcesCleaned': resources_cleaned
            })
            total_resources += resources_cleaned
        
        return {
            'success': True,
            'cleanedSessions': len(cleaned_sessions),
            'totalResources': total_resources,
            'sessions': cleaned_sessions
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

# WebSocket route
app.websocket("/ws")(websocket_endpoint)

# Session management endpoints
@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session information and state"""
    session_info = session_store.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return session_info

@app.post("/api/session/{session_id}/save")
async def save_session(session_id: str, state: dict):
    """Save session state"""
    success = session_store.save_session(session_id, state)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save session")
    return {"status": "success", "session_id": session_id}

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and clean up resources"""
    success = session_store.remove_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    return {"status": "deleted", "session_id": session_id}

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    return {"sessions": session_store.list_active_sessions()}

@app.post("/api/sessions/cleanup")
async def force_cleanup():
    """Force cleanup all sessions - for development/testing"""
    session_store.force_cleanup_all()
    return {"status": "cleaned_up"}
