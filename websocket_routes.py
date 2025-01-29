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
    cleanup_workflow,
    handle_file_upload
)
import asyncio

active_connections: List[WebSocket] = []

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
    user_directory = f"./user_data/{uid}"

    active_connections.append(websocket)
    state = initialize_state(uid)

    # try:
    await websocket.send_json({"type": "connected", "uid": uid}) 
    
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        command = data.get('command')

        if command == 'retry':
            # Handle retry after rate limit
            retry_command = data.get('retry_command')
            retry_data = data.get('retry_data')
            await handle_command(websocket, state, retry_command, retry_data)
        else:
            await handle_command(websocket, state, command, data)

    # except WebSocketDisconnect:
        # print("Connection closed")
        # active_connections.remove(websocket)
    # except Exception as e:
    #     print(f"ERROR:: {str(e)} ::ERROR")
    #     await websocket.send_json({'type': 'error', 'message': str(e)})