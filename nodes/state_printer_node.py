

def state_printer(state):
    """print the state"""
    print("---STATE PRINTER---")
    print(f"Initial Prompt: {state['initial_prompt']} \n" )
    print(f"Search Term: {state['search_term']} \n")
    # print(f"Draft Email: {state['draft_email']} \n" )
    # print(f"Final Email: {state['final_email']} \n" )
    # print(f"Research Info: {state['research_info']} \n")
    # print(f"RAG Questions: {state['rag_questions']} \n")
    print(f"Num Steps: {state['num_steps']} \n")
    return