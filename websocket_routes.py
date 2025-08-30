from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import os
from uuid import uuid4
import copy
from state_manager import initialize_state
from session_store import session_store
from command_handlers import (
    start_conversation,
    handle_user_input,
    handle_user_search_term,
    handle_continue_search,
    cleanup_workflow,
    handle_file_upload
)
import asyncio

active_connections: List[WebSocket] = []

def clean_state_for_serialization(state):
    """Remove non-serializable objects from state before saving"""
    clean_state = {}
    
    # Only copy serializable data types
    for key, value in state.items():
        # Skip internal keys and WebSocket objects
        if key.startswith('_'):
            continue
        
        # Skip functions and other non-serializable objects
        if hasattr(value, '__call__'):
            continue
            
        # Check if value is JSON serializable by attempting to serialize it
        try:
            import json
            json.dumps(value)  # Test if it can be serialized
            clean_state[key] = value
        except (TypeError, ValueError):
            # Skip non-serializable values
            print(f"Skipping non-serializable key: {key}")
            continue
    
    return clean_state

def validate_recovery_state(state):
    """Validate that the recovered state has essential data for recovery"""
    if not state or not isinstance(state, dict):
        return False
    
    # Check for essential fields that indicate a recoverable session
    essential_fields = ['uid']
    for field in essential_fields:
        if field not in state:
            return False
    
    # Check for at least some meaningful progress
    has_progress = (
        state.get('chat_history') and len(state.get('chat_history', [])) > 0 or
        state.get('medical_report') or
        state.get('search_term') and len(state.get('search_term', [])) > 0 or
        state.get('studies_found', 0) > 0
    )
    
    return has_progress

async def send_recovery_status(websocket: WebSocket, state):
    """Send current state information to frontend after recovery"""
    try:
        # Send current node status
        current_node = state.get('next_step', 'consultant')
        await websocket.send_json({
            'type': 'status',
            'message': f'Session recovered - resuming from {current_node}',
            'current_step': current_node,
            'current_node': current_node
        })
        
        # If we have a medical report, send it to restore UI display
        if state.get('medical_report'):
            await websocket.send_json({
                'type': 'report',
                'content': state['medical_report']
            })
        
        # Send any existing search term suggestions
        if state.get('search_term') and len(state.get('search_term', [])) > 0:
            # Send the search term as a suggestion to restore the search UI
            search_terms = state['search_term']
            if isinstance(search_terms, list) and len(search_terms) > 0:
                await websocket.send_json({
                    'type': 'new_search_term',
                    'content': ', '.join(search_terms)
                })
        
        # Send any existing studies found count
        if state.get('studies_found', 0) > 0:
            await websocket.send_json({
                'type': 'studies_found',
                'content': f"Recovered session with {state['studies_found']} trials found",
                'state': {'studies_found_count': state['studies_found']}
            })
            
        # If we have research info, indicate analysis was completed
        if state.get('research_info'):
            await websocket.send_json({
                'type': 'research_info',
                'state': {'research_info': state['research_info']}
            })
            
    except Exception as e:
        print(f"Error sending recovery status: {e}")

def should_resume_workflow(state):
    """Determine if workflow should be automatically resumed after recovery"""
    # Don't resume if workflow was already completed
    if state.get('next_step') == 'state_printer':
        return False
        
    # Don't resume if we're waiting for user input
    waiting_for_user_steps = ['consultant', 'search_term']
    if state.get('next_step') in waiting_for_user_steps:
        return False
        
    # Resume if we were in the middle of processing
    processing_steps = ['prompt_distiller', 'trials_search', 'research_info_search', 'evaluate_research_info']
    return state.get('next_step') in processing_steps

async def resume_workflow(websocket: WebSocket, state):
    """Resume workflow from where it left off"""
    try:
        next_step = state.get('next_step', 'consultant')
        print(f"Resuming workflow from step: {next_step}")
        
        # Send status update
        await websocket.send_json({
            'type': 'status', 
            'message': f'Resuming workflow from {next_step}...',
            'current_step': next_step
        })
        
        # For now, we'll handle basic resumption
        # More complex workflow resumption would require integrating with the LangGraph workflow
        # This is a simplified approach that works with the current architecture
        
        if next_step == 'trials_search' and state.get('search_term'):
            # Resume trial search if we have search terms but no studies found yet
            if not state.get('studies_found') or state.get('studies_found') == 0:
                await websocket.send_json({
                    'type': 'status',
                    'message': 'Resuming clinical trials search...'
                })
        
        elif next_step == 'research_info_search' and state.get('studies_found', 0) > 0:
            # Resume research info search if we have studies but no research info
            if not state.get('research_info'):
                await websocket.send_json({
                    'type': 'status',
                    'message': 'Resuming trial analysis...'
                })
        
        elif next_step == 'evaluate_research_info' and state.get('research_info'):
            # Resume evaluation if we have research info
            await websocket.send_json({
                'type': 'status',
                'message': 'Completing trial evaluation...'
            })
            
    except Exception as e:
        print(f"Error resuming workflow: {e}")

async def heartbeat(websocket: WebSocket, interval: int = 30):
    try:
        while True:
            await asyncio.sleep(interval)
            # Check if WebSocket is still open before sending
            try:
                if websocket.client_state.name == 'CONNECTED':
                    await websocket.send_json({"type": "ping"})
                else:
                    print("WebSocket not connected, stopping heartbeat")
                    break  # Stop heartbeat if connection is closed
            except Exception as send_error:
                # Connection was closed during send attempt
                print(f"Heartbeat send failed, stopping: {send_error}")
                break
    except asyncio.CancelledError:
        print("Heartbeat cancelled")
        raise  # Re-raise cancellation
    except Exception as e:
        # Connection was closed or errored, stop heartbeat
        print(f"Heartbeat stopped: {e}")
        pass

async def handle_command(websocket: WebSocket, state, command, data):
    try:
        if command == 'start':
            await start_conversation(websocket, state)
        elif command == 'upload':
            await handle_file_upload(websocket, state, data)
        elif command == 'user_input':
            await handle_user_input(websocket, state, data.get('input', ''))
        elif command == 'user_search_term':
            await handle_user_search_term(websocket, state, data.get('search_term', '').strip())
        elif command == 'continue_search':
            await handle_continue_search(websocket, state, data.get('keep_searching'))
        elif command == 'cleanup':
            await cleanup_workflow(websocket, state)
    except Exception as e:
        if "429" in str(e).lower():
            await websocket.send_json({
                'type': 'rate_limit_error',
                'message': str(e),
                'retry_command': command,
                'retry_data': data
            })
        else:
            raise e

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    uid = websocket.query_params.get("uid")
    is_recovery = websocket.query_params.get("recover") == "true"
    recovery_successful = False
    
    # Try to recover session state if requested
    if is_recovery:
        session_data = session_store.load_session(uid)
        if session_data and session_data.get('state'):
            try:
                # Load existing state from session store and merge with fresh state
                recovered_state = session_data['state']
                state = initialize_state(uid)
                
                # Validate essential recovery data
                if validate_recovery_state(recovered_state):
                    # Merge recovered data into fresh state
                    for key, value in recovered_state.items():
                        if not key.startswith('_'):  # Don't restore internal keys
                            state[key] = value
                    
                    state['uid'] = uid  # Ensure UID is set
                    recovery_successful = True
                    print(f"Session {uid} recovered successfully with state: {state.get('next_step', 'consultant')}")
                else:
                    print(f"Invalid recovery state for session {uid}, starting fresh")
                    state = initialize_state(uid)
            except Exception as e:
                print(f"Error during session recovery for {uid}: {e}")
                state = initialize_state(uid)
        else:
            # Fallback to new state if recovery fails
            print(f"No valid session data found for {uid}, starting fresh")
            state = initialize_state(uid)
    else:
        state = initialize_state(uid)
    
    active_connections.append(websocket)
    
    # Don't store websocket in state - keep it separate to avoid serialization issues
    # state['_websocket'] = websocket  # REMOVED - causes JSON serialization errors
    # state['_connected_at'] = asyncio.get_event_loop().time()  # REMOVED

    await websocket.send_json({"type": "connected", "uid": uid, "recovered": recovery_successful})
    
    # Send recovery status and current state information
    if recovery_successful:
        await send_recovery_status(websocket, state)
    
    # Resume workflow if recovery was successful and workflow was in progress
    if recovery_successful and should_resume_workflow(state):
        await resume_workflow(websocket, state)

    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat(websocket))

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            command = data.get('command')

            if command == 'retry':
                await handle_command(websocket, state, data.get('retry_command'), data.get('retry_data'))
            else:
                await handle_command(websocket, state, command, data)
                
                # Save state after each command (clean state for serialization)
                try:
                    clean_state = clean_state_for_serialization(state)
                    session_store.update_session(uid, clean_state)
                except Exception as save_error:
                    print(f"Warning: Could not save session state for {uid}: {save_error}")
                    # Don't fail the command if session save fails
                
    except WebSocketDisconnect:
        print(f"Client {uid} disconnected.")
    except Exception as e:
        print(f"WebSocket error for {uid}: {e}")
    finally:
        heartbeat_task.cancel()
        if websocket in active_connections:
            active_connections.remove(websocket)
        
        # Save final state on disconnect
        try:
            # Clean state for serialization
            clean_state = clean_state_for_serialization(state)
            session_store.update_session(uid, clean_state)
            print(f"Session state saved for {uid}")
        except Exception as e:
            print(f"Error saving session state for {uid}: {e}")
    # except WebSocketDisconnect:
        # print("Connection closed")
        # active_connections.remove(websocket)
    # except Exception as e:
    #     print(f"ERROR:: {str(e)} ::ERROR")
    #     await websocket.send_json({'type': 'error', 'message': str(e)})