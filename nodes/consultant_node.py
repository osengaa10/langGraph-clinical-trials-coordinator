from chains.consultant_chain import consultant_chain
from utils import write_markdown_file

# def consultant(state):
#     chat_history = state.get("chat_history", [])
    
#     if not chat_history:
#         # Start the conversation if chat_history is empty
#         initial_question = consultant_chain.invoke({
#             "chat_history": [],
#             "initial_prompt": "Ask the patient what their medical issue is."
#         })
#         print(f"AI: {initial_question}")
#         user_response = input("User: ")
#         chat_history = [
#             {"role": "assistant", "content": initial_question},
#             {"role": "user", "content": user_response}
#         ]
    
#     for _ in range(2):  # Ask 2 more questions (3 total including the initial one)
#         initial_prompt = "\n".join(msg['content'] for msg in chat_history)
#         response = consultant_chain.invoke({
#             "chat_history": chat_history,
#             "initial_prompt": initial_prompt
#         })
        
#         print(f"AI: {response}")
#         user_response = input("User: ")
        
#         chat_history.append({"role": "assistant", "content": response})
#         chat_history.append({"role": "user", "content": user_response})
    
#     num_steps = int(state['num_steps'])
#     num_steps += 1
#     # Generate a medical summary
#     initial_prompt = "\n".join(msg['content'] for msg in chat_history)
#     summary = consultant_chain.invoke({
#         "chat_history": chat_history,
#         "initial_prompt": initial_prompt
#     })
    
#     state["chat_history"] = chat_history
#     state["medical_report"] = summary
#     write_markdown_file(summary, "medical_report")
    
#     return state


def consultant(state):
    chat_history = state.get("chat_history", [])
    num_steps = int(state.get('num_steps', 0))
    num_steps += 1
    
    if not chat_history:
        # Start the conversation if chat_history is empty
        initial_question = consultant_chain.invoke({
            "chat_history": [],
            "initial_prompt": "Ask the patient what their medical issue is."
        })
        print(f"AI: {initial_question}")
        user_response = input("User: ")
        chat_history = [
            {"role": "assistant", "content": initial_question},
            {"role": "user", "content": user_response}
        ]
    
    for _ in range(2):  # Ask 2 more questions (3 total including the initial one)
        initial_prompt = "\n".join(msg['content'] for msg in chat_history)
        response = consultant_chain.invoke({
            "chat_history": chat_history,
            "initial_prompt": initial_prompt
        })
        
        print(f"AI: {response}")
        user_response = input("User: ")
        
        chat_history.append({"role": "assistant", "content": response})
        chat_history.append({"role": "user", "content": user_response})
    
    # Generate a medical summary
    initial_prompt = "\n".join(msg['content'] for msg in chat_history)
    summary = consultant_chain.invoke({
        "chat_history": chat_history,
        "initial_prompt": "Based on the conversation, provide a concise medical report."
    })
    
    state["chat_history"] = chat_history
    state["medical_report"] = summary
    state["num_steps"] = num_steps
    write_markdown_file(summary, "medical_report")
    
    return state