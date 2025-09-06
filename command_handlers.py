from nodes.consultant_node import consultant_chain, format_chat_history
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
        filename = data.get('filename', 'clinical_notes.pdf')
        
        # Send initial upload status
        await websocket.send_json({
            'type': 'status',
            'message': f'Processing {filename}...',
            'activity': {
                'id': 'file_processing',
                'title': 'File Processing',
                'description': f'Reading and extracting text from {filename}',
                'status': 'active'
            },
            'current_step': 'consultant'
        })
        
        # Extract and decode PDF
        pdf_data = data.get('data', '')
        pdf_bytes = base64.b64decode(pdf_data)
        
        # Complete file processing and start text extraction
        await websocket.send_json({
            'type': 'activity_update',
            'activity': {
                'id': 'file_processing',
                'status': 'completed'
            }
        })
        
        await websocket.send_json({
            'type': 'status',
            'message': 'Extracting text from PDF...',
            'activity': {
                'id': 'text_extraction',
                'title': 'PDF Text Extraction',
                'description': 'Converting PDF pages to readable text format',
                'status': 'active'
            },
            'current_step': 'consultant'
        })
        
        # Extract text from PDF
        text = ""
        with BytesIO(pdf_bytes) as pdf_file:
            reader = PdfReader(pdf_file)
            total_pages = len(reader.pages)
            for page_num, page in enumerate(reader.pages, 1):
                text += page.extract_text() + "\n"
                # Send progress update for longer PDFs
                if total_pages > 3 and page_num % 2 == 0:
                    await websocket.send_json({
                        'type': 'status',
                        'message': f'Processing page {page_num} of {total_pages}...',
                        'activity': {
                            'title': 'PDF Text Extraction',
                            'description': f'Processing page {page_num} of {total_pages}',
                            'status': 'active'
                        },
                        'progress': min(10 + (page_num / total_pages * 20), 30),
                        'current_step': 'consultant'
                    })
        
        # Complete text extraction
        await websocket.send_json({
            'type': 'activity_update',
            'activity': {
                'id': 'text_extraction',
                'status': 'completed',
                'description': f'Successfully extracted text from {total_pages} pages'
            }
        })
        
        # Store in state and update chat history
        state['clinical_notes'] = text
        state['chat_history'].append({"role": "user", "content": text})
        await generate_report(websocket, state)
        
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'content': f'Failed to process PDF: {str(e)}',
            'activity': {
                'title': 'File Processing Error',
                'description': f'Error processing {filename}: {str(e)}',
                'status': 'error'
            }
        })
        raise e

async def generate_report(websocket, state):
    # Send status update for report generation
    await websocket.send_json({
        'type': 'status',
        'message': 'Analyzing medical information and generating comprehensive report...',
        'activity': {
            'title': 'Medical Report Generation',
            'description': 'AI is creating a comprehensive medical summary from your information',
            'status': 'active'
        },
        'current_step': 'consultant'
    })
    
    if 'clinical_notes' in state:
        report_content = state['clinical_notes']
        summary = consultant_chain["report"].invoke({
            "chat_history": [{"role": "user", "content": report_content}]
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
        'current_step': 'consultant',
        'next_node': 'prompt_distiller',
        'state': state
    })
    await handle_prompt_distiller(websocket, state)



async def handle_prompt_distiller(websocket, state):
    distiller_response = prompt_distiller_chain.invoke({
        "medical_report": state['medical_report'],
        "existing_terms": ", ".join(state['search_term'])
    })
    
    # Extract the first search term as the new_search_term for compatibility
    new_search_term = distiller_response.search_terms[0].term if distiller_response.search_terms else "clinical trial"
    
    # Store the full response for potential future use
    state['distiller_response'] = distiller_response.dict()
    state['new_search_term'] = new_search_term
    
    await websocket.send_json({
        'type': 'new_search_term',
        'content': new_search_term,
        'current_node': 'prompt_distiller',
        'current_step': 'prompt_distiller',
        'state': state
    })


async def handle_user_search_term(websocket: WebSocket, state, user_search_term):
    if user_search_term and user_search_term not in state['search_term']:

        state['search_term'].append(user_search_term)
        await websocket.send_json({
            'type': 'search_term_added',
            'content': user_search_term,
            'current_step': 'trials_search',
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
    start_time = asyncio.get_event_loop().time()

    # While it's running, send more detailed status updates
    status_count = 0
    while not task.done():
        status_count += 1
        elapsed_time = int(asyncio.get_event_loop().time() - start_time)
        
        if status_count == 1:
            message = "Deep-analyzing trial eligibility criteria..."
        elif status_count == 2:
            message = "Cross-referencing your medical profile with trial requirements..."
        elif status_count == 3:
            message = "AI is performing comprehensive eligibility assessment..."
        else:
            message = f"Still evaluating trials (elapsed: {elapsed_time}s)..."
            
        await websocket.send_json({
            "type": "status",
            "activity": {
                "title": "Eligibility Analysis in Progress",
                "description": message,
                "status": "active"
            },
            "custom_message": message,
            "progress": min(85 + (elapsed_time / 10), 95)
        })
        await asyncio.sleep(15)  # More frequent updates

    evaluation_result = await task
    state['follow_up'] = evaluation_result

    if "A suitable clinical trial was found:" in evaluation_result:
        await websocket.send_json({
            'type': 'trials_found',
            'content': state['research_info'][0],
            'current_node': 'evaluate_research_info',
            'current_step': 'evaluate_research_info',
            'next_node': 'user_decision',
            'progress': 100,
            'activity': {
                'title': 'Suitable Trials Found!',
                'description': 'AI has identified clinical trials that match your eligibility criteria',
                'status': 'completed'
            },
            'custom_message': 'Great news! We found suitable clinical trials for you.',
            'state': state
        })
        await asyncio.sleep(0.1)
        state['next_step'] = 'state_printer'
    else:
        await websocket.send_json({
            'type': 'no_trial_found',
            'content': state['follow_up'],
            'current_node': 'evaluate_research_info',
            'current_step': 'evaluate_research_info',
            'next_node': 'consultant',
            'progress': 100,
            'activity': {
                'title': 'Analysis Complete',
                'description': 'No fully matching trials found. Consider expanding search criteria.',
                'status': 'completed'
            },
            'custom_message': 'Analysis complete. Let\'s explore other options for you.',
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
    start_time = asyncio.get_event_loop().time()
    update_count = 0
    
    while not embed_task.done():
        update_count += 1
        elapsed_time = int(asyncio.get_event_loop().time() - start_time)
        estimated_progress = min(35 + (elapsed_time / 8), 48)  # Progress from 35% to 48%
        
        if update_count == 1:
            message = f"Processing {len(studies_found)} trial documents..."
        elif update_count == 2:
            message = "Creating searchable vectors from trial data..."
        elif update_count == 3:
            message = "Building AI knowledge base from clinical trials..."
        else:
            message = f"Still processing documents (elapsed: {elapsed_time}s)..."
            
        await websocket.send_json({
            'type': 'status',
            'activity': {
                'title': 'Document Processing',
                'description': message,
                'status': 'active'
            },
            'custom_message': message,
            'progress': estimated_progress,
            'current_step': 'trials_search'
        })
        await asyncio.sleep(20)  # More frequent updates

    await embed_task


async def continue_workflow(websocket: WebSocket, state):
    state['next_step'] = 'trials_search'
    
    while state['next_step'] != 'state_printer':
        current_node = state['next_step']
        
        if current_node == 'trials_search':
            # Send initial search activity
            await websocket.send_json({
                'type': 'status',
                'activity': {
                    'title': 'Searching Clinical Trials Database',
                    'description': 'Querying ClinicalTrials.gov for matching studies...',
                    'status': 'active'
                },
                'current_step': 'trials_search',
                'custom_message': 'Searching ClinicalTrials.gov database...'
            })
            
            trials_search_result = trials_search(state)
            studies_found_count = trials_search_result['studies_found_count']
            studies_found = trials_search_result['studies_found']
            uid = trials_search_result['uid']
            next_step = trials_search_result['next_step']
            search_attempt_count = trials_search_result['search_attempt_count']
            
            # Update state with all results
            state.update(trials_search_result)
            
            if studies_found_count == 0:
                print("none found")
                await websocket.send_json({
                    'type': 'need_new_term',
                    'content': 'no studies found',
                    'current_node': current_node,
                    'activity': {
                        'title': 'No Trials Found',
                        'description': 'No trials found with current search terms. Please try different terms.',
                        'status': 'completed'
                    },
                    'state': state
                })
                await asyncio.sleep(0.1)
                break
            elif next_step == "prompt_distiller":
                # Retry scenario: less than 100 trials found, need new search term
                await websocket.send_json({
                    'type': 'retry_search',
                    'content': f'Found {studies_found_count} trials (< 100). Generating new search term...',
                    'current_node': current_node,
                    'current_step': 'prompt_distiller',
                    'next_node': 'prompt_distiller',
                    'progress': 15,
                    'activity': {
                        'title': f'Retry Search (Attempt {search_attempt_count})',
                        'description': f'Found {studies_found_count} trials. Generating new search term...',
                        'status': 'active',
                        'stats': {'Trials Found': studies_found_count, 'Attempt': search_attempt_count}
                    },
                    'state': state
                })
                await asyncio.sleep(0.5)
                
                # Continue to prompt_distiller node
                state['next_step'] = 'prompt_distiller'
            else:
                # Sufficient trials found (>= 100), continue to research
                await websocket.send_json({
                    'type': 'studies_found',
                    'content': 'Clinical trials search completed',
                    'current_node': current_node,
                    'current_step': 'trials_search',
                    'next_node': 'research_info_search',
                    'progress': 25,
                    'activity': {
                        'title': f'Found {studies_found_count} Clinical Trials',
                        'description': f'Retrieved {studies_found_count} potential trials from the database',
                        'status': 'completed',
                        'stats': {'Trials Found': studies_found_count}
                    },
                    'state': state
                })
                await asyncio.sleep(0.1)
                
                await websocket.send_json({
                    'type': 'embedding_studies',
                    'content': 'Processing trial documents for AI analysis',
                    'current_node': current_node,
                    'current_step': 'trials_search',
                    'next_node': 'research_info_search',
                    'progress': 35,
                    'activity': {
                        'title': 'Processing Trial Documents',
                        'description': 'Converting trial documents into AI-searchable format...',
                        'status': 'active'
                    },
                    'custom_message': f'Processing {studies_found_count} trial documents for AI analysis...',
                    'state': state
                })
                await asyncio.sleep(0.1)
                
                print("beginning to embed!!")
                await monitor_embed(websocket, studies_found, uid)
                print(f"embedded {studies_found_count} trials!")

                await websocket.send_json({
                    'type': 'status',
                    'activity': {
                        'title': 'Document Processing Complete',
                        'description': f'Successfully processed {studies_found_count} trial documents',
                        'status': 'completed'
                    },
                    'progress': 50,
                    'current_step': 'trials_search'
                })

                state['next_step'] = 'research_info_search'

        elif current_node == 'prompt_distiller':
            # Handle retry search term generation
            await websocket.send_json({
                'type': 'status',
                'activity': {
                    'title': f'Generating New Search Term (Attempt {state.get("search_attempt_count", 1)})',
                    'description': 'AI is creating alternative search terms to find more trials...',
                    'status': 'active'
                },
                'current_step': 'prompt_distiller',
                'progress': 10,
                'custom_message': f'Generating new search term (attempt {state.get("search_attempt_count", 1)})...'
            })
            
            from nodes.prompt_distiller_node import prompt_distiller
            prompt_distiller_result = prompt_distiller(state)
            state.update(prompt_distiller_result)
            
            await websocket.send_json({
                'type': 'new_search_term',
                'content': f'Generated new search term: {state["search_term"][-1]}',
                'current_node': current_node,
                'current_step': 'prompt_distiller',
                'next_node': 'trials_search',
                'progress': 12,
                'activity': {
                    'title': 'New Search Term Ready',
                    'description': f'Generated: "{state["search_term"][-1]}"',
                    'status': 'completed'
                },
                'state': state
            })
            
            state['next_step'] = 'trials_search'

        elif current_node == 'research_info_search':
            await websocket.send_json({
                'type': 'status',
                'activity': {
                    'title': 'Analyzing Trial Relevance',
                    'description': 'AI is analyzing trials to find the best matches for your profile...',
                    'status': 'active'
                },
                'current_step': 'research_info_search',
                'progress': 60,
                'custom_message': 'AI is analyzing trial relevance to your medical profile...'
            })
            
            research_info_result = research_info_search(state)
            state.update(research_info_result)
            
            await websocket.send_json({
                'type': 'research_info',
                'content': 'Research info search completed',
                'current_node': current_node,
                'current_step': 'research_info_search',
                'next_node': 'evaluate_research_info',
                'progress': 75,
                'activity': {
                    'title': 'Trial Matching Complete',
                    'description': 'AI has identified the most relevant trials for your condition',
                    'status': 'completed'
                },
                'state': state
            })
            await asyncio.sleep(0.1)
            state['next_step'] = 'evaluate_research_info'

        elif current_node == 'evaluate_research_info':
            await websocket.send_json({
                'type': 'status',
                'activity': {
                    'title': 'Verifying Eligibility',
                    'description': 'Performing final eligibility checks and preparing recommendations...',
                    'status': 'active'
                },
                'current_step': 'evaluate_research_info',
                'progress': 85,
                'custom_message': 'Verifying trial eligibility and preparing personalized recommendations...'
            })
            
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
    from session_store import session_store
    
    uid = state['uid']
    cleanup_results = []
    cleanup_errors = []
    
    try:
        # Send initial cleanup status
        await websocket.send_json({
            'type': 'status',
            'message': 'Starting session cleanup...',
            'current_step': 'state_printer'
        })
        
        # 1. Clean up RAG data directory
        rag_path = os.path.join('./rag_data/data', uid)
        if os.path.exists(rag_path) and os.path.isdir(rag_path):
            try:
                shutil.rmtree(rag_path)
                cleanup_results.append(f"Cleaned RAG data: {rag_path}")
                print(f"Successfully deleted RAG directory: {rag_path}")
            except Exception as e:
                cleanup_errors.append(f"Failed to clean RAG data: {e}")
                print(f"Error deleting RAG directory {rag_path}: {e}")

        # 2. Clean up database directory
        db_path = os.path.join('./db', uid)
        if os.path.exists(db_path) and os.path.isdir(db_path):
            try:
                shutil.rmtree(db_path)
                cleanup_results.append(f"Cleaned database: {db_path}")
                print(f"Successfully deleted DB directory: {db_path}")
            except Exception as e:
                cleanup_errors.append(f"Failed to clean database: {e}")
                print(f"Error deleting DB directory {db_path}: {e}")

        # 3. Clean up studies directory
        studies_path = os.path.join('./studies', uid)
        if os.path.exists(studies_path) and os.path.isdir(studies_path):
            try:
                shutil.rmtree(studies_path)
                cleanup_results.append(f"Cleaned studies: {studies_path}")
                print(f"Successfully deleted studies directory: {studies_path}")
            except Exception as e:
                cleanup_errors.append(f"Failed to clean studies: {e}")
                print(f"Error deleting studies directory {studies_path}: {e}")

        # 4. Remove session from session store
        try:
            success = session_store.remove_session(uid)
            if success:
                cleanup_results.append("Removed session from store")
                print(f"Successfully removed session {uid} from session store")
            else:
                cleanup_errors.append("Failed to remove session from store")
        except Exception as e:
            cleanup_errors.append(f"Error removing session from store: {e}")
            print(f"Error removing session {uid} from store: {e}")

        # Send cleanup completion status
        if cleanup_errors:
            await websocket.send_json({
                'type': 'cleanup_complete',
                'success': False,
                'content': f'Cleanup completed with errors. Success: {len(cleanup_results)}, Errors: {len(cleanup_errors)}',
                'results': cleanup_results,
                'errors': cleanup_errors,
                'state': state
            })
        else:
            await websocket.send_json({
                'type': 'cleanup_complete',
                'success': True,
                'content': f'Session cleanup completed successfully. Cleaned {len(cleanup_results)} resources.',
                'results': cleanup_results,
                'state': state
            })

        # Send final workflow complete message
        await websocket.send_json({
            'type': 'workflow_complete',
            'content': 'Session ended and cleaned up successfully',
            'current_node': 'state_printer',
            'next_node': None
        })

    except Exception as e:
        print(f"Critical error during cleanup for session {uid}: {e}")
        await websocket.send_json({
            'type': 'cleanup_error',
            'content': f'Critical cleanup error: {str(e)}',
            'state': state
        })
    