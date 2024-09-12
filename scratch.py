from typing import Dict
from langchain_core.output_parsers import StrOutputParser
from LLMs.llm import GROQ_LLM
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import Graph, StateType

# Define the prompt template
prompt = ChatPromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a top medical doctor, and you will ask questions to a patient about
    their condition. Your questions are designed to get all the necessary information
    to determine which clinical trials are the best fit for the patient.
     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Ask the patient questions about their condition to gather enough information
    to write a paragraph long medical report. Your medical report will be read
    by other doctors.


            Output a one paragraph medical report about patient's condition.

    PATIENT PROMPT:\n\n {initial_prompt} \n\n
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["initial_prompt"],
)

# Create the consultant chain
consultant_chain = prompt | GROQ_LLM | StrOutputParser()

# Define the node function
def medical_conversation_node(state: Dict) -> Dict:
    # Extract chat history from the state
    chat_history = state.get("chat_history", [])
    
    # Conduct a brief Q&A with the user
    for _ in range(3):  # Ask up to 3 questions
        # Generate a question based on the chat history
        question = consultant_chain.invoke({"initial_prompt": "\n".join(chat_history)})
        
        # Get user's response
        print(f"AI: {question}")
        user_response = input("User: ")
        
        # Update chat history
        chat_history.extend([question, user_response])
    
    # Generate a medical summary
    summary = consultant_chain.invoke({"initial_prompt": "\n".join(chat_history)})
    
    # Update the state with the chat history and summary
    state["chat_history"] = chat_history
    state["medical_summary"] = summary
    
    return state

# Create the graph
workflow = Graph()

# Add the medical conversation node to the graph
workflow.add_node("medical_conversation", medical_conversation_node)

# Set the entrypoint of the graph
workflow.set_entry_point("medical_conversation")

# Compile the graph
app = workflow.compile()

# Run the graph
initial_state = {"chat_history": []}
final_state = app.invoke(initial_state)

# Print the medical summary
print("\nMedical Summary:")
print(final_state["medical_summary"])