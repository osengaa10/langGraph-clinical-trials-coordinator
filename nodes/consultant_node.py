from chains.consultant_chain import consultant_chain
from utils import write_markdown_file

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
    num_steps = int(state.get('num_steps', 0))
    num_steps += 1
    
    if not chat_history:
        # Start the conversation if chat_history is empty
        initial_question = consultant_chain["conversation"].invoke({
            "chat_history": [],
            "initial_prompt": "Ask the patient what their medical issue is."
        })
        print(f"AI: {initial_question} \n")
        user_response = input("User: ")
        chat_history = [
            {"role": "assistant", "content": initial_question},
            {"role": "user", "content": user_response}
        ]
    else:
        # If we're coming back from a failed trial search or for more information
        follow_up = state.get("follow_up", "")
        if follow_up:
            prompt = f"Based on our previous conversation and the following additional information needed: {follow_up}, ask a relevant follow-up question."
        else:
            prompt = "Based on our previous conversation, ask a relevant follow-up question to gather more information about the patient's condition."
        
        response = consultant_chain["conversation"].invoke({
            "chat_history": chat_history,
            "initial_prompt": prompt
        })
        print(f"\nAI: {response} \n")
        user_response = input("User: ")
        chat_history.append({"role": "assistant", "content": response})
        chat_history.append({"role": "user", "content": user_response})
    
    # Ask additional questions
    for _ in range(2):  # Ask 2 more questions
        prompt = "Based on the conversation so far, ask another relevant question to gather more information about the patient's condition."
        response = consultant_chain["conversation"].invoke({
            "chat_history": chat_history,
            "initial_prompt": prompt
        })
        
        print(f"\n AI: {response} \n")
        user_response = input("User: ")
        
        chat_history.append({"role": "assistant", "content": response})
        chat_history.append({"role": "user", "content": user_response})
    
    # Generate a medical summary
    summary = consultant_chain["report"].invoke({
        "chat_history": chat_history
    })
    
    print(f"AI: Based on our conversation, here's a summary of your medical report:\n{summary}\n")
    
    state["chat_history"] = chat_history
    state["medical_report"] = summary
    state["num_steps"] = num_steps
    state["follow_up"] = ""  # Clear the follow-up after it's been addressed
    
    # Format and write chat history
    formatted_chat_history = format_chat_history(chat_history)
    write_markdown_file(formatted_chat_history, "chat_history")
    
    write_markdown_file(summary, "medical_report")
    
    return state