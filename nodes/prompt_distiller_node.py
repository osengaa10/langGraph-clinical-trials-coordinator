from chains.prompt_distiller_chain import prompt_distiller_chain
from utils import write_markdown_file

def prompt_distiller(state):
    """take the initial prompt and return a unique search term"""
    print("---DISTILLING INITIAL PROMPT---")
    medical_report = state['medical_report']
    num_steps = int(state['num_steps'])
    num_steps += 1

    # Retrieve the current search terms from the state
    current_search_terms = state.get("search_term", [])
    
    # Ensure current_search_terms is a list
    if isinstance(current_search_terms, str):
        current_search_terms = [current_search_terms]
    elif current_search_terms is None:
        current_search_terms = []

    # Generate a new search term and check for duplicates
    max_attempts = 3  # Limit the number of attempts to avoid infinite loops
    for _ in range(max_attempts):
        new_search_term = prompt_distiller_chain.invoke({
            "medical_report": medical_report,
            "existing_terms": ", ".join(current_search_terms)
        })
        print("___NEW SEARCH TERM___ ", new_search_term)
        
        if new_search_term not in current_search_terms:
            current_search_terms.append(new_search_term)
            break
        else:
            print(f"Search term '{new_search_term}' already exists. Generating a new one...")
    
    # Update the state with the new list of search terms
    updated_state = dict(state)  # Create a new copy of the state
    updated_state["search_term"] = current_search_terms
    updated_state["num_steps"] = num_steps
    
    # Save to local disk
    write_markdown_file(", ".join(current_search_terms), "search_terms")

    print("___ALL SEARCH TERMS___", current_search_terms)

    # Return the updated state
    return updated_state