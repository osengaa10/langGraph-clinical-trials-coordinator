from chains.consultant_chain import consultant_chain
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
    chat_history = state.get("chat_history", [])
    if chat_history is None:
        chat_history = []

    num_steps = int(state.get('num_steps', 0))
    num_steps += 1
    print(f"chat_history:: {chat_history}")
    if not chat_history:
        # Start the conversation if chat_history is empty
        initial_prompt = "Ask the patient what their medical issue is."
    else:
        # If we're coming back from a failed trial search or for more information
        follow_up = state.get("follow_up", "")
        if follow_up:
            initial_prompt = f"Based on our previous conversation and the following additional information needed: {follow_up}, ask a relevant follow-up question."
        else:
            initial_prompt = "Based on our previous conversation, ask a relevant follow-up question to gather more information about the patient's condition."

    while True:
        response = consultant_chain["conversation"].invoke({
            "chat_history": chat_history,  # This will now always be a list, even if empty
            "initial_prompt": initial_prompt
        })
        
        if isinstance(response, str):
            # If the response is a string, try to parse it as JSON
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                print("Error: Unable to parse response as JSON. Continuing with next question.")
                continue

        if response.get('action') == 'ask_question':
            print(f"\nAI: {response.get('content', 'No question provided')} \n")
            user_response = input("User: ")
            chat_history.append({"role": "assistant", "content": response.get('content', 'No question provided')})
            chat_history.append({"role": "user", "content": user_response})
            initial_prompt = "Continue the conversation based on the patient's response."
        elif response.get('action') == 'generate_report':
            print(f"\nAI: {response.get('content', 'Ready to generate report')} \n")
            break
        else:
            print("Error: Invalid action received. Continuing with next question.")
    
    # Generate a medical summary
    summary = consultant_chain["report"].invoke({
        "chat_history": chat_history
    })
    
    print(f"AI: Based on our conversation, here's a summary of your medical report:\n{summary}\n")
    
    state["chat_history"] = chat_history
    state["medical_report"] = summary
    state["num_steps"] = num_steps
    state["follow_up"] = ""  
    
    # Format and write chat history
    formatted_chat_history = format_chat_history(chat_history)
    write_markdown_file(formatted_chat_history, "chat_history")
    
    write_markdown_file(summary, "medical_report")
    
    return state