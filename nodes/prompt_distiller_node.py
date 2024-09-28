from chains.prompt_distiller_chain import prompt_distiller_chain
from utils import write_markdown_file

def prompt_distiller(state):
    """take the initial prompt and return a search term"""
    print("---DISTILLING INITIAL PROMPT---")
    medical_report = state['medical_report']
    num_steps = int(state['num_steps'])
    num_steps += 1

    search_term = prompt_distiller_chain.invoke({"medical_report": medical_report})
    print("___SEARCH TERM___ ", search_term)
    # save to local disk
    write_markdown_file(search_term, "search_term")

    # Add the new search term to the list
    current_search_terms = state.get("search_term", [])
    if isinstance(current_search_terms, str):
        current_search_terms = [current_search_terms]
    elif current_search_terms is None:
        current_search_terms = []
    
    current_search_terms.append(search_term)

    return {"search_term": current_search_terms, "num_steps": num_steps}