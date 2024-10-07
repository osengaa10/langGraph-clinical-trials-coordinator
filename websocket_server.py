import asyncio
import websockets
import json
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
                await start_conversation(websocket, state)
                print(f"state: {state}")
            elif command == 'user_input':
                await handle_user_input(websocket, state, data.get('input', ''))
                print(f"state: {state}")

            elif command == 'search_term_decision':
                await handle_search_term_decision(websocket, state, data.get('decision'))
                print(f"state: {state}")

            elif command == 'user_search_term':
                await handle_user_search_term(websocket, state, data.get('search_term', '').strip())
                print(f"state: {state}")

            elif command == 'continue_search':
                await handle_continue_search(websocket, state, data.get('decision'))
                print(f"state: {state}")

    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed")
    except Exception as e:
        print(f"Error: {str(e)}")
        await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))

async def start_conversation(websocket, state):
    response = consultant_chain["conversation"].invoke({
        "chat_history": state['chat_history'],
        "initial_prompt": "Ask the patient what their medical issue is."
    })
    
    state['chat_history'].append({"role": "assistant", "content": response['content']})
    await websocket.send(json.dumps({
        'type': 'question',
        'content': response['content'],
        'state': state
    }))

async def handle_user_input(websocket, state, user_input):
    state['chat_history'].append({"role": "user", "content": user_input})
    
    response = consultant_chain["conversation"].invoke({
        "chat_history": state['chat_history'],
        "initial_prompt": "Continue the conversation based on the patient's response."
    })

    if response.get('action') == 'ask_question':
        state['chat_history'].append({"role": "assistant", "content": response['content']})
        await websocket.send(json.dumps({
            'type': 'question',
            'content': response['content'],
            'current_node': 'consultant',
            'next_node': 'user_input',
            'state': state
        }))
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
        'next_node': 'prompt_distiller',
        'state': state
    }))
    await handle_prompt_distiller(websocket, state)


async def handle_prompt_distiller(websocket, state):
    # max_attempts = 3
    # for _ in range(max_attempts):
    new_search_term = prompt_distiller_chain.invoke({
        "medical_report": state['medical_report'],
        "existing_terms": ", ".join(state['search_term'])
    })
    state['new_search_term'] = new_search_term
    await websocket.send(json.dumps({
        'type': 'new_search_term',
        'content': new_search_term,
        'state': state
    }))
        # Wait for user decision in the main loop

async def handle_search_term_decision(websocket, state, decision):
    if decision == 'yes':
        if state['new_search_term'] not in state['search_term']:
            state['search_term'].append(state['new_search_term'])
            await websocket.send(json.dumps({
                'type': 'search_term_added',
                'content': state['new_search_term'],
                'state': state
            }))
            await continue_workflow(websocket, state)
        else:
            await websocket.send(json.dumps({
                'type': 'search_term_exists',
                'content': state['new_search_term'],
                'state': state
            }))
            await handle_prompt_distiller(websocket, state)
    elif decision == 'no':
        await websocket.send(json.dumps({
            'type': 'request_user_search_term',
            'state': state
        }))
    else:
        await websocket.send(json.dumps({
            'type': 'invalid_input',
            'state': state
        }))

async def handle_user_search_term(websocket, state, user_search_term):
    if user_search_term and user_search_term not in state['search_term']:
        state['search_term'].append(user_search_term)
        await websocket.send(json.dumps({
            'type': 'search_term_added',
            'content': user_search_term,
            'state': state
        }))
        await continue_workflow(websocket, state)
    elif user_search_term in state['search_term']:
        await websocket.send(json.dumps({
            'type': 'search_term_exists',
            'content': user_search_term,
            'state': state
        }))
        await handle_prompt_distiller(websocket, state)
    else:
        await websocket.send(json.dumps({
            'type': 'invalid_input',
            'state': state
        }))

async def continue_workflow(websocket, state):
    state['next_step'] = 'trials_search'
    
    while state['next_step'] != 'state_printer':
        current_node = state['next_step']
        
        if current_node == 'trials_search':
            trials_search_result = trials_search(state)
            state.update(trials_search_result)
            await websocket.send(json.dumps({
                'type': 'update',
                'content': 'Clinical trials search completed',
                'current_node': current_node,
                'next_node': 'research_info_search',
                'state': state
            }))
            state['next_step'] = 'research_info_search'

        elif current_node == 'research_info_search':
            research_info_result = research_info_search(state)
            state.update(research_info_result)
            await websocket.send(json.dumps({
                'type': 'update',
                'content': 'Research info search completed',
                'current_node': current_node,
                'next_node': 'evaluate_research_info',
                'state': state
            }))
            state['next_step'] = 'evaluate_research_info'

        elif current_node == 'evaluate_research_info':
            evaluation_result = evaluate_research_info(state)
            state.update(evaluation_result)
            
            if "A suitable clinical trial was found:" in state['research_info'][0]:
                await websocket.send(json.dumps({
                    'type': 'trial_found',
                    'content': state['research_info'][0],
                    'current_node': current_node,
                    'next_node': 'user_decision',
                    'state': state
                }))
                break
            else:
                await websocket.send(json.dumps({
                    'type': 'no_trial_found',
                    'content': state['follow_up'],
                    'current_node': current_node,
                    'next_node': 'consultant',
                    'state': state
                }))
                state['next_step'] = 'consultant'

        elif current_node == 'consultant':
            await websocket.send(json.dumps({
                'type': 'update',
                'content': 'Returning to consultant for follow-up',
                'current_node': current_node,
                'next_node': 'user_input',
                'state': state
            }))
            await start_conversation(websocket, state)
            break

    if state['next_step'] == 'state_printer':
        await websocket.send(json.dumps({
            'type': 'workflow_complete',
            'content': 'Workflow completed',
            'current_node': 'state_printer',
            'next_node': None
        }))

async def handle_continue_search(websocket, state, decision):
    if decision == 'yes':
        state['next_step'] = 'consultant'
        state['follow_up'] = "Let's explore more options. Can you provide any additional details about your condition or preferences for treatment?"
        await start_conversation(websocket, state)
    else:
        state['next_step'] = 'state_printer'
        await continue_workflow(websocket, state)

async def main():
    server = await websockets.serve(handle_websocket, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())