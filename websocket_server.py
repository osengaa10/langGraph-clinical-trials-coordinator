import asyncio
import websockets
import json
from graph import create_workflow, GraphState
from LLMs.llm import GROQ_LLM
from dotenv import load_dotenv
from nodes.consultant_node import consultant_chain, format_chat_history
from utils import write_markdown_file

load_dotenv()

app = create_workflow(GROQ_LLM)

async def handle_websocket(websocket, path):
    try:
        state = GraphState(
            medical_report="",
            search_term=[],
            chat_history=[],
            final_medical_report="",
            research_info=[],
            follow_up="",
            num_steps=0,
            next_step="consultant",
            draft_email_feedback={},
            rag_questions=[]
        )

        await websocket.send(json.dumps({"type": "connected"}))

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            command = data.get('command')

            if command == 'start':
                # Start the conversation
                response = consultant_chain["conversation"].invoke({
                    "chat_history": state['chat_history'],
                    "initial_prompt": "Ask the patient what their medical issue is."
                })
                
                state['chat_history'].append({"role": "assistant", "content": response['content']})
                await websocket.send(json.dumps({
                    'type': 'question',
                    'content': response['content']
                }))

            elif command == 'user_input':
                user_input = data.get('input', '')
                state['chat_history'].append({"role": "user", "content": user_input})
                
                # Continue the conversation
                response = consultant_chain["conversation"].invoke({
                    "chat_history": state['chat_history'],
                    "initial_prompt": "Continue the conversation based on the patient's response."
                })

                if response.get('action') == 'ask_question':
                    state['chat_history'].append({"role": "assistant", "content": response['content']})
                    await websocket.send(json.dumps({
                        'type': 'question',
                        'content': response['content']
                    }))
                elif response.get('action') == 'generate_report':
                    # Generate a medical summary
                    summary = consultant_chain["report"].invoke({
                        "chat_history": state['chat_history']
                    })
                    
                    state["medical_report"] = summary
                    state["num_steps"] += 1
                    
                    # Format and write chat history
                    formatted_chat_history = format_chat_history(state['chat_history'])
                    write_markdown_file(formatted_chat_history, "chat_history")
                    write_markdown_file(summary, "medical_report")
                    
                    await websocket.send(json.dumps({
                        'type': 'report',
                        'content': summary
                    }))

                    # Continue with the rest of the workflow
                    for output in app.stream(state):
                        state.update(output)
                        await websocket.send(json.dumps({
                            'type': 'update',
                            'chat_history': format_chat_history(state['chat_history']),
                            'current_step': state['next_step']
                        }))

                        if state['next_step'] == 'state_printer':
                            break

    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed")
    except Exception as e:
        print(f"Error: {str(e)}")
        await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))

async def main():
    server = await websockets.serve(handle_websocket, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())