import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uuid import uuid4
from typing import Dict

from graph import create_workflow
from LLMs.llm import GROQ_LLM

app = FastAPI(
    title="LangGraph Workflow API",
    version="1.0",
    description="API for running the LangGraph workflow",
)

# Create the workflow
workflow = create_workflow(GROQ_LLM)

# Store active sessions
active_sessions: Dict[str, Dict] = {}

class SessionStart(BaseModel):
    initial_input: Dict

@app.post("/start_session")
async def start_session(session_start: SessionStart):
    session_id = str(uuid4())
    active_sessions[session_id] = {
        "workflow": workflow,
        "state": {"num_steps": 0, **session_start.initial_input}
    }
    return {"session_id": session_id}

@app.websocket("/workflow/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in active_sessions:
        await websocket.send_json({"error": "Invalid session ID"})
        await websocket.close()
        return

    session = active_sessions[session_id]
    
    try:
        while True:
            # Run the next step of the workflow
            result = await asyncio.to_thread(session["workflow"].invoke, session["state"])
            
            # Send the result to the client
            await websocket.send_json({"result": result})
            
            # Check if the workflow is complete
            if "final_medical_report" in result:
                break
            
            # Wait for user input if needed
            if result.get("next_step") == "consultant":
                user_input = await websocket.receive_text()
                session["state"]["chat_history"] += f"\nHuman: {user_input}"
            
            # Update the session state
            session["state"].update(result)
    
    except WebSocketDisconnect:
        del active_sessions[session_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)