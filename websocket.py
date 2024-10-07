import asyncio
import websockets
import json
import traceback
from graph import create_workflow, GraphState
from LLMs.llm import GROQ_LLM
from dotenv import load_dotenv
from nodes.consultant_node import consultant_chain, format_chat_history
from nodes.prompt_distiller_node import prompt_distiller_chain
from nodes.trials_search_node import trials_search
from nodes.rag_node import research_info_search
from nodes.evaluate_trials_node import evaluate_research_info
from utils import write_markdown_file

load_dotenv()

print("Initializing app...")
app = create_workflow(GROQ_LLM)
print("App initialized.")

async def handle_websocket(websocket, path):
    try:
        print("New websocket connection established.")
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
        print("Sent 'connected' message to client.")

        while True:
            message = await websocket.recv()
            print(f"Received message: {message}")
            data = json.loads(message)
            command = data.get('command')

            print(f"Processing command: {command}")

            if command == 'start':
                print("Starting workflow...")
                await continue_workflow(websocket, state)
                print(f"state:: {state}")
            elif command == 'user_input':
                print(f"Received user input: {data.get('input', '')}")
                state['chat_history'].append({"role": "user", "content": data.get('input', '')})
                await continue_workflow(websocket, state)
                print(f"state:: {state}")
            elif command == 'search_term_decision':
                print(f"Received search term decision: {data.get('decision')}")
                if data.get('decision') == 'yes':
                    state['search_term'].append(state['new_search_term'])
                await continue_workflow(websocket, state)
            elif command == 'continue_search':
                print(f"Received continue search decision: {data.get('decision')}")
                if data.get('decision') == 'yes':
                    state['next_step'] = 'consultant'
                else:
                    state['next_step'] = 'state_printer'
                await continue_workflow(websocket, state)

    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed")
    except Exception as e:
        print(f"Error in handle_websocket: {str(e)}")
        traceback.print_exc()
        await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))

async def continue_workflow(websocket, state):
    print(f"Continuing workflow from step: {state['next_step']}")
    try:
        for output in app.stream(state):
            print(f"Received output from app.stream: {output}")
            state.update(output)
            current_node = state['next_step']
            
            await websocket.send(json.dumps({
                'type': 'update',
                'content': f'Completed step: {current_node}',
                'current_node': current_node,
                'next_node': state['next_step']
            }))
            print(f"Sent update for step: {current_node}")

            if current_node == 'consultant':
                await handle_consultant_node(websocket, state)
            elif current_node == 'prompt_distiller':
                await handle_prompt_distiller(websocket, state)
            elif current_node == 'trials_search':
                await handle_trials_search(websocket, state)
            elif current_node == 'research_info_search':
                await handle_research_info_search(websocket, state)
            elif current_node == 'evaluate_research_info':
                await handle_evaluate_research_info(websocket, state)
            elif current_node == 'state_printer':
                await websocket.send(json.dumps({
                    'type': 'workflow_complete',
                    'content': 'Workflow completed',
                    'current_node': 'state_printer',
                    'next_node': None
                }))
                print("Workflow completed.")
                break
            else:
                print(f"Unknown node: {current_node}")
    except Exception as e:
        print(f"Error in continue_workflow: {str(e)}")
        traceback.print_exc()
        await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))

async def handle_consultant_node(websocket, state):
    print("Handling consultant node")
    if state['chat_history']:
        print("Chat history exists, handling user input")
        await handle_user_input(websocket, state, state['chat_history'][-1]['content'])
    else:
        print("Starting new conversation")
        await start_conversation(websocket, state)

async def start_conversation(websocket, state):
    print("Starting conversation")
    try:
        response = consultant_chain["conversation"].invoke({
            "chat_history": state['chat_history'],
            "initial_prompt": "Ask the patient what their medical issue is."
        })
        print(f"LLM response: {response}")
    except Exception as e:
        print(f"Error in LLM call: {str(e)}")
        traceback.print_exc()
        raise
    
    state['chat_history'].append({"role": "assistant", "content": response['content']})
    await websocket.send(json.dumps({
        'type': 'question',
        'content': response['content'],
        'current_node': 'consultant',
        'next_node': 'user_input'
    }))
    print("Sent question to client")

async def handle_user_input(websocket, state, user_input):
    print(f"Handling user input: {user_input}")
    try:
        response = consultant_chain["conversation"].invoke({
            "chat_history": state['chat_history'],
            "initial_prompt": "Continue the conversation based on the patient's response."
        })
        print(f"LLM response: {response}")
    except Exception as e:
        print(f"Error in LLM call: {str(e)}")
        traceback.print_exc()
        raise

    if response.get('action') == 'ask_question':
        state['chat_history'].append({"role": "assistant", "content": response['content']})
        await websocket.send(json.dumps({
            'type': 'question',
            'content': response['content'],
            'current_node': 'consultant',
            'next_node': 'user_input'
        }))
        print("Sent follow-up question to client")
    elif response.get('action') == 'generate_report':
        await generate_report(websocket, state)

async def generate_report(websocket, state):
    summary = consultant_chain["report"].invoke({
        "chat_history": state['chat_history']
    })
    
    state["medical_report"] = summary
    state["num_steps"] += 1
    
    formatted_chat_history = format_chat_history(state['chat_history'])
    write_markdown_file(formatted_chat_history, "chat_history")
    write_markdown_file(summary, "medical_report")
    
    await websocket.send(json.dumps({
        'type': 'report',
        'content': summary,
        'current_node': 'consultant',
        'next_node': 'prompt_distiller'
    }))

async def handle_prompt_distiller(websocket, state):
    new_search_term = prompt_distiller_chain.invoke({
        "medical_report": state['medical_report'],
        "existing_terms": ", ".join(state['search_term'])
    })
    state['new_search_term'] = new_search_term
    await websocket.send(json.dumps({
        'type': 'new_search_term',
        'content': new_search_term,
        'current_node': 'prompt_distiller',
        'next_node': 'user_decision'
    }))

async def handle_trials_search(websocket, state):
    trials_search_result = trials_search(state)
    state.update(trials_search_result)
    await websocket.send(json.dumps({
        'type': 'update',
        'content': 'Clinical trials search completed',
        'current_node': 'trials_search',
        'next_node': state['next_step']
    }))

async def handle_research_info_search(websocket, state):
    research_info_result = research_info_search(state)
    state.update(research_info_result)
    await websocket.send(json.dumps({
        'type': 'update',
        'content': 'Research info search completed',
        'current_node': 'research_info_search',
        'next_node': state['next_step']
    }))

async def handle_evaluate_research_info(websocket, state):
    evaluation_result = evaluate_research_info(state)
    state.update(evaluation_result)
    
    if "A suitable clinical trial was found:" in state['research_info'][0]:
        await websocket.send(json.dumps({
            'type': 'trial_found',
            'content': state['research_info'][0],
            'current_node': 'evaluate_research_info',
            'next_node': 'user_decision'
        }))
    else:
        await websocket.send(json.dumps({
            'type': 'no_trial_found',
            'content': state['follow_up'],
            'current_node': 'evaluate_research_info',
            'next_node': state['next_step']
        }))

async def main():
    server = await websockets.serve(handle_websocket, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())