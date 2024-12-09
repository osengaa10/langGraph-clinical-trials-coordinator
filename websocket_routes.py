from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import os
from uuid import uuid4
from state_manager import initialize_state
from command_handlers import (
    start_conversation,
    handle_user_input,
    handle_user_search_term,
    handle_continue_search,
    cleanup_workflow
)

active_connections: List[WebSocket] = []

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Extract UID from the query parameter
    uid = websocket.query_params.get("uid")  
    user_directory = f"./user_data/{uid}"

    active_connections.append(websocket)
    state = initialize_state(uid)

    try:
        await websocket.send_json({"type": "connected", "uid": uid}) 
        
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            command = data.get('command')

            if command == 'start':
                await start_conversation(websocket, state)
            elif command == 'user_input':
                await handle_user_input(websocket, state, data.get('input', ''))
            elif command == 'user_search_term':
                await handle_user_search_term(websocket, state, data.get('search_term', '').strip())
            elif command == 'continue_search':
                await handle_continue_search(websocket, state, data.get('keep_searching'))
            elif command == 'cleanup':
                await cleanup_workflow(websocket, state)

    except WebSocketDisconnect:
        print("Connection closed")
        active_connections.remove(websocket)
    except Exception as e:
        print(f"ERROR:: {str(e)} ::ERROR")
        await websocket.send_json({'type': 'error', 'message': str(e)})
