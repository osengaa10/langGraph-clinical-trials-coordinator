from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
from state_manager import initialize_state
from command_handlers import (
    start_conversation,
    handle_user_input,
    handle_search_term_decision,
    handle_user_search_term,
    handle_continue_search
)

active_connections: List[WebSocket] = []

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    state = initialize_state()

    try:
        await websocket.send_json({"type": "connected"})
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            command = data.get('command')

            if command == 'start':
                await start_conversation(websocket, state)
            elif command == 'user_input':
                await handle_user_input(websocket, state, data.get('input', ''))
            elif command == 'search_term_decision':
                await handle_search_term_decision(websocket, state, data.get('decision'))
            elif command == 'user_search_term':
                await handle_user_search_term(websocket, state, data.get('search_term', '').strip())
            elif command == 'continue_search':
                await handle_continue_search(websocket, state, data.get('keep_searching'))

    except WebSocketDisconnect:
        print("Connection closed")
        active_connections.remove(websocket)
    except Exception as e:
        print(f"ERROR:: {str(e)} ::ERROR")
        await websocket.send_json({'type': 'error', 'message': str(e)})
