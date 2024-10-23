from nodes.consultant_node import consultant_chain, format_chat_history
from nodes.prompt_distiller_node import prompt_distiller_chain
from utils import write_markdown_file
from fastapi import WebSocket
# from workflow_handler import continue_workflow
from nodes.trials_search_node import trials_search 
from nodes.rag_node import research_info_search
from nodes.evaluate_trials_node import evaluate_research_info, evaluate_trials_chain
import asyncio

async def start_conversation(websocket: WebSocket, state):
    chat_history = state.get("chat_history", [])
    initial_prompt = ""
    if not chat_history:
        initial_prompt = "Ask the patient what their medical issue is."
    else:
        # If we're coming back from a failed trial search or for more information
        follow_up = state.get("follow_up", "")
        if follow_up:
            initial_prompt = f"Based on our previous conversation and the following additional information needed: {follow_up}, ask a relevant follow-up question."
        else:
            initial_prompt = "Based on our previous conversation, ask a relevant follow-up question to gather more information about the patient's condition."

    print(f"initial_prompt:: {initial_prompt}")
    response = consultant_chain["conversation"].invoke({
        "chat_history": state['chat_history'],
        "initial_prompt": initial_prompt
    })
    state['chat_history'].append({"role": "assistant", "content": response['content']})
    await websocket.send_json({
        'type': 'question',
        'content': response['content'],
        'state': state
    })


async def handle_user_input(websocket, state, user_input):
    state['chat_history'].append({"role": "user", "content": user_input})
    
    response = consultant_chain["conversation"].invoke({
        "chat_history": state['chat_history'],
        "initial_prompt": "Continue the conversation based on the patient's response."
    })

    if response.get('action') == 'ask_question':
        state['chat_history'].append({"role": "assistant", "content": response['content']})
        await websocket.send_json({
            'type': 'question',
            'content': response['content'],
            'current_node': 'consultant',
            'next_node': 'user_input',
            'state': state
        })
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
    await websocket.send_json({
        'type': 'report',
        'content': summary,
        'current_node': 'consultant',
        'next_node': 'prompt_distiller',
        'state': state
    })
    await handle_prompt_distiller(websocket, state)



async def handle_prompt_distiller(websocket, state):
    new_search_term = prompt_distiller_chain.invoke({
        "medical_report": state['medical_report'],
        "existing_terms": ", ".join(state['search_term'])
    })
    state['new_search_term'] = new_search_term
    await websocket.send_json({
        'type': 'new_search_term',
        'content': new_search_term,
        'current_node': 'prompt_distiller',
        'state': state
    })



async def handle_search_term_decision(websocket: WebSocket, state, decision):
    if decision == 'yes':
        if state['new_search_term'] not in state['search_term']:
            state['search_term'].append(state['new_search_term'])
            await websocket.send_json({
                'type': 'search_term_added',
                'content': state['new_search_term'],
                'state': state
            })
            await continue_workflow(websocket, state)
        else:
            await websocket.send_json({
                'type': 'search_term_exists',
                'content': state['new_search_term'],
                'state': state
            })
            await handle_prompt_distiller(websocket, state)
    elif decision == 'no':
        await websocket.send_json({
            'type': 'request_user_search_term',
            'state': state
        })
    else:
        await websocket.send_json({
            'type': 'invalid_input',
            'state': state
        })


async def handle_user_search_term(websocket: WebSocket, state, user_search_term):
    if user_search_term and user_search_term not in state['search_term']:

        state['search_term'].append(user_search_term)
        await websocket.send_json({
            'type': 'search_term_added',
            'content': user_search_term,
            'state': state
        })
        await asyncio.sleep(0.1)
        await continue_workflow(websocket, state)
    elif user_search_term in state['search_term']:
        await websocket.send_json({
            'type': 'search_term_exists',
            'content': user_search_term,
            'state': state
        })
        await handle_prompt_distiller(websocket, state)
    else:
        await websocket.send_json({
            'type': 'invalid_input',
            'state': state
        })

async def handle_evaluate_trials(websocket: WebSocket, state):
    research_info = state['research_info']
    evaluation_result = evaluate_trials_chain.invoke({"research_info": research_info})
    print(f"evaluation_result:: {evaluation_result}")
    if "A suitable clinical trial was found:" in evaluation_result:
        await websocket.send_json({
            'type': 'trials_found',
            'content': state['research_info'][0],
            'current_node': 'evaluate_trials',
            'next_node': 'user_decision',
            'state': state
        })
        await asyncio.sleep(0.1)
        state['next_step'] = 'state_printer'
    else:
        await websocket.send_json({
            'type': 'no_trial_found',
            'content': state['follow_up'],
            'current_node': 'evaluate_trials',
            'next_node': 'consultant',
            'state': state
        })
        await asyncio.sleep(0.1)
        state['next_step'] = 'consultant'


async def handle_continue_search(websocket: WebSocket, state, decision):
    state['keep_searching'] = 'yes'
    if decision == 'yes':
        state['next_step'] = 'consultant'
        # state['keep_searching'] = 'yes'
        state['follow_up'] = "Let's explore more options. Can you provide any additional details about your condition or preferences for treatment?"
        await start_conversation(websocket, state)
    else:
        # state['keep_searching'] = 'no'
        state['next_step'] = 'state_printer'
        await continue_workflow(websocket, state)


async def continue_workflow(websocket: WebSocket, state):
    state['next_step'] = 'trials_search'
    
    while state['next_step'] != 'state_printer':
        current_node = state['next_step']
        
        if current_node == 'trials_search':
            trials_search_result = trials_search(state)
            state.update(trials_search_result)
            print(f"trials_search_result:: {trials_search_result}")
            await websocket.send_json({
                'type': 'update',
                'content': 'Clinical trials search completed',
                'current_node': current_node,
                'next_node': 'research_info_search',
                'state': state
            })
            await asyncio.sleep(0.1)
            state['next_step'] = 'research_info_search'

        elif current_node == 'research_info_search':
            research_info_result = research_info_search(state)
            state.update(research_info_result)
            await websocket.send_json({
                'type': 'research_info',
                'content': 'Research info search completed',
                'current_node': current_node,
                'next_node': 'evaluate_research_info',
                'state': state
            })
            await asyncio.sleep(0.1)
            state['next_step'] = 'evaluate_research_info'

        elif current_node == 'evaluate_research_info':
            await handle_evaluate_trials(websocket, state)

        elif current_node == 'consultant':
            await websocket.send_json({
                'type': 'update',
                'content': 'Returning to consultant for follow-up',
                'current_node': current_node,
                'next_node': 'user_input',
                'state': state
            })
            await asyncio.sleep(0.1)
            await start_conversation(websocket, state)
            break

    if state['next_step'] == 'state_printer':
        await websocket.send_json({
            'type': 'workflow_complete',
            'content': 'Workflow completed',
            'current_node': 'state_printer',
            'next_node': None
        })