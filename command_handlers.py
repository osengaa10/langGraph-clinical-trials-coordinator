from nodes.consultant_node import consultant_chain, format_chat_history, clinical_notes_chain
from nodes.prompt_distiller_node import prompt_distiller_chain
from utils import write_markdown_file
from fastapi import WebSocket
from nodes.trials_search_node import trials_search 
from nodes.rag_node import research_info_search
from rag import chunk_and_embed
from nodes.evaluate_trials_node import evaluate_research_info, evaluate_trials_chain
import asyncio
import os
import shutil
from PyPDF2 import PdfReader
from io import BytesIO
from fastapi.concurrency import run_in_threadpool

import base64

async def start_conversation(websocket: WebSocket, state):
    chat_history = state.get("chat_history", [])
    clinical_notes = state.get("clinical_notes", [])

    initial_prompt = ""
    if not chat_history or not clinical_notes:
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
            'current_step': 'consultant',
            'next_node': 'user_input',
            'state': state
        })
    elif response.get('action') == 'generate_report':
        await generate_report(websocket, state)



async def handle_file_upload(websocket, state, data):
    try:
        # Extract and decode PDF
        pdf_data = data.get('data', '')
        filename = data.get('filename', 'clinical_notes.pdf')
        pdf_bytes = base64.b64decode(pdf_data)
        
        # Extract text from PDF
        text = ""
        with BytesIO(pdf_bytes) as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        # Store in state and update chat history
        state['clinical_notes'] = text
        state['chat_history'].append({"role": "user", "content": text})
        await generate_report(websocket, state)
        
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'content': f'Failed to process PDF: {str(e)}'
        })
        raise e

async def generate_report(websocket, state):
    if 'clinical_notes' in state:
        report_content = state['clinical_notes']
        summary = clinical_notes_chain["report"].invoke({
            "clinical_notes": report_content
        })
        write_markdown_file(str(report_content), "clinical_notes")

    else:
        formatted_chat_history = format_chat_history(state['chat_history'])
        summary = consultant_chain["report"].invoke({
            "chat_history": state['chat_history']
        })
        write_markdown_file(formatted_chat_history, "chat_history")

    state["medical_report"] = summary
    state["num_steps"] += 1
    write_markdown_file(summary, "medical_report")
    await websocket.send_json({
        'type': 'report',
        'content': summary,
        'current_node': 'consultant',
        'current_step': 'medical_report',
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
        'current_step': 'search_term',
        'state': state
    })


async def handle_user_search_term(websocket: WebSocket, state, user_search_term):
    if user_search_term and user_search_term not in state['search_term']:

        state['search_term'].append(user_search_term)
        await websocket.send_json({
            'type': 'search_term_added',
            'content': user_search_term,
            'current_step': 'fetch_trials',
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

    # Start the long-running trial evaluation as a background task
    async def run_chain():
        return evaluate_trials_chain.invoke({"research_info": research_info})

    task = asyncio.create_task(run_chain())

    # While it’s running, send a ping/status every 30s to keep the connection alive
    while not task.done():
        await websocket.send_json({
            "type": "status",
            "message": "Evaluating trials... please wait."
        })
        await asyncio.sleep(30)

    evaluation_result = await task
    state['follow_up'] = evaluation_result

    if "A suitable clinical trial was found:" in evaluation_result:
        await websocket.send_json({
            'type': 'trials_found',
            'content': state['research_info'][0],
            'current_node': 'evaluate_trials',
            'current_step': 'verify_eligibility',
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
            'current_step': 'verify_eligibility',
            'next_node': 'consultant',
            'state': state
        })
        await asyncio.sleep(0.1)
        state['next_step'] = 'consultant'

async def handle_continue_search(websocket: WebSocket, state, decision):
    if decision == 'yes':
        state['next_step'] = 'consultant'
        state['follow_up'] = "Let's explore more options. Can you provide any additional details about your condition or preferences for treatment?"
        await start_conversation(websocket, state)
    else:
        state['next_step'] = 'state_printer'
        await websocket.send_json({
                'type': 'workflow_complete',
                'content': 'Workflow completed',
                'current_node': 'state_printer',
                'next_node': None
            })            

async def monitor_embed(websocket: WebSocket, studies_found, uid):
    embed_task = asyncio.create_task(run_in_threadpool(chunk_and_embed, studies_found, uid))
    
    while not embed_task.done():
        await websocket.send_json({
            'type': 'status',
            'message': 'Embedding studies... please wait.'
        })
        await asyncio.sleep(30)  # Keep Cloudflare happy

    await embed_task


async def continue_workflow(websocket: WebSocket, state):
    state['next_step'] = 'trials_search'
    
    while state['next_step'] != 'state_printer':
        current_node = state['next_step']
        
        if current_node == 'trials_search':
            trials_search_result = trials_search(state)
            studies_found_count = trials_search_result['studies_found_count']
            studies_found = trials_search_result['studies_found']
            uid = trials_search_result['uid']
            if studies_found_count == 0:
                print("none found")
                await websocket.send_json({
                    'type': 'need_new_term',
                    'content': 'no studies found',
                    'current_node': current_node,
                    'state': state
                })
                await asyncio.sleep(0.1)
                break
            else:
                state.update(trials_search_result)
                await websocket.send_json({
                    'type': 'studies_found',
                    'content': 'Clinical trials search completed',
                    'current_node': current_node,
                    'current_step': 'fetch_trials',
                    'next_node': 'research_info_search',
                    'state': state
                })
                await asyncio.sleep(0.1)
                await websocket.send_json({
                    'type': 'embedding_studies',
                    'content': 'Clinical trials search completed',
                    'current_node': current_node,
                    'current_step': 'embed_trials',
                    'next_node': 'research_info_search',
                    'state': state
                })
                await asyncio.sleep(0.1)
                print("beginning to embed!!")
                await monitor_embed(websocket, studies_found, uid)
                print(f"embedded {studies_found_count} trials!")

                state['next_step'] = 'research_info_search'

        elif current_node == 'research_info_search':
            research_info_result = research_info_search(state)
            state.update(research_info_result)
            await websocket.send_json({
                'type': 'research_info',
                'content': 'Research info search completed',
                'current_node': current_node,
                'current_step': 'matching_trials',
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



async def cleanup_workflow(websocket: WebSocket, state):
    uid = state['uid']
    base_path = './rag_data/data'
    user_path = os.path.join(base_path, uid)
    db_base_path = './db'
    db_path = os.path.join(db_base_path, uid)

    if (os.path.exists(user_path) and os.path.isdir(user_path)) or (os.path.exists(db_path) and os.path.isdir(db_path)):
        try:
            if os.path.exists(user_path) and os.path.isdir(user_path):
                shutil.rmtree(user_path)
                print(f"Successfully deleted the directory: {user_path}")
            else:
                print(f"The directory {user_path} does not exist.")

            if os.path.exists(db_path) and os.path.isdir(db_path):
                shutil.rmtree(db_path)
                print(f"Successfully deleted the directory: {db_path}")
            else:
                print(f"The directory {db_path} does not exist.")

            await websocket.send_json({
                'type': 'cleanup',
                'content': f'deleted {user_path} and {db_path}',
                'state': state
            })
            await asyncio.sleep(0.1) 
        except Exception as e:
            print(f"An error occurred while deleting the directories: {e}")
            await websocket.send_json({
                'type': 'cleanup',
                'content': f'error occurred: {e}',
                'state': state
            })
    