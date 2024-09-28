from chains.prompt_distiller_chain import prompt_distiller_chain
from utils import write_markdown_file

def prompt_distiller(state):
    """take the initial prompt and return a search term"""
    print("---DISTILLING INITIAL PROMPT---")
    medical_report = state['medical_report']
    num_steps = int(state['num_steps'])
    num_steps += 1

    new_search_term = prompt_distiller_chain.invoke({"medical_report": medical_report})
    print("___NEW SEARCH TERM___ ", new_search_term)
    
    # Retrieve the current search terms from the state
    current_search_terms = state.get("search_term", [])
    
    # Ensure current_search_terms is a list
    if isinstance(current_search_terms, str):
        current_search_terms = [current_search_terms]
    elif current_search_terms is None:
        current_search_terms = []
    
    # Append the new search term
    current_search_terms.append(new_search_term)
    
    # Update the state with the new list of search terms
    state["search_term"] = current_search_terms
    
    # Save to local disk (optional: you might want to save the full list instead)
    write_markdown_file(", ".join(current_search_terms), "search_terms")

    print("___ALL SEARCH TERMS___", current_search_terms)

    # Return the updated state
    return {**state, "num_steps": num_steps}