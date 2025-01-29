from chains.consultant_chain import consultant_chain
from chains.clinical_notes_chain import clinical_notes_chain
from utils import write_markdown_file
import json

def format_chat_history(chat_history):
    formatted_chat = ""
    for message in chat_history:
        if message['role'] == 'assistant':
            formatted_chat += f"AI: {message['content']}\n\n"
        elif message['role'] == 'user':
            formatted_chat += f"User: {message['content']}\n\n"
    return formatted_chat

def consultant(state):
    # Check for clinical notes first
    if 'clinical_notes' in state and state['clinical_notes']:
        # Directly generate report from clinical notes
        summary = clinical_notes_chain["report"].invoke({
            "clinical_notes": state['clinical_notes']
        })
        
        print(f"AI: Generated medical report from clinical notes:\n{summary}\n")
        
        # Update state
        state["medical_report"] = summary
        state["num_steps"] = state.get('num_steps', 0) + 1
        
        # Format and write outputs
        formatted_notes = f"Clinical Notes:\n{state['clinical_notes']}"
        write_markdown_file(formatted_notes, "clinical_notes")
        write_markdown_file(summary, "medical_report")
        
        return state
    else:
        # Original conversation flow
        chat_history = state.get("chat_history", []) or []
        num_steps = state.get('num_steps', 0) + 1

        print(f"chat_history:: {chat_history}")
        
        if not chat_history:
            initial_prompt = "Ask the patient what their medical issue is."
        else:
            follow_up = state.get("follow_up", "")
            initial_prompt = (f"Based on our previous conversation{' and additional information needed: ' + follow_up if follow_up else ''}, "
                            "ask a relevant follow-up question.")

        while True:
            response = consultant_chain["conversation"].invoke({
                "chat_history": chat_history,
                "initial_prompt": initial_prompt
            })
            
            # Handle response parsing
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    print("Error: Invalid response format. Continuing...")
                    continue

            action = response.get('action')
            
            if action == 'ask_question':
                print(f"\nAI: {response.get('content', 'No question provided')} \n")
                user_response = input("User: ")
                chat_history.extend([
                    {"role": "assistant", "content": response['content']},
                    {"role": "user", "content": user_response}
                ])
                initial_prompt = "Continue the conversation based on the patient's response."
            elif action == 'generate_report':
                print(f"\nAI: {response.get('content', 'Ready to generate report')} \n")
                break
            else:
                print("Error: Invalid action received. Continuing...")
                continue

        # Generate summary from conversation
        summary = consultant_chain["report"].invoke({
            "chat_history": chat_history
        })
        
        print(f"AI: Conversation-based medical report:\n{summary}\n")
        
        # Update state
        state.update({
            "chat_history": chat_history,
            "medical_report": summary,
            "num_steps": num_steps,
            "follow_up": ""
        })
        
        # Write outputs
        write_markdown_file(format_chat_history(chat_history), "chat_history")
        write_markdown_file(summary, "medical_report")
        
        return state