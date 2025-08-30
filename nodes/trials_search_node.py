from utils import clinical_trials_search, write_markdown_file

def trials_search(state):
    """make api call to search for trials"""
    print("---FETCHING CLINICAL TRIALS---")
    search_term = state['search_term'][-1]
    num_steps = int(state['num_steps'])
    num_steps += 1
    uid = state['uid']
    
    # Get current attempt count, default to 1 if not set
    search_attempt_count = state.get('search_attempt_count', 1)

    print("___UID___ ", uid)
    print(f"___SEARCH ATTEMPT {search_attempt_count}___")
    studies_found = clinical_trials_search(search_term.replace("\"", ""), uid)
    studies_found_count = len(studies_found)

    # save to local disk
    write_markdown_file(search_term, "search_term")

    # Determine next step based on trial count and attempt count
    max_attempts = 5
    min_trials = 100
    
    if studies_found_count < min_trials and search_attempt_count < max_attempts:
        print(f"Found {studies_found_count} trials (< {min_trials}). Retry with new search term.")
        next_step = "prompt_distiller"
        search_attempt_count += 1
    elif studies_found_count >= min_trials:
        print(f"Found {studies_found_count} trials (>= {min_trials}). Continuing to research.")
        next_step = "research_info_search"
    else:
        print(f"Max attempts ({max_attempts}) reached with {studies_found_count} trials. Continuing anyway.")
        next_step = "research_info_search"

    return {
        "search_term": state['search_term'], 
        "num_steps": num_steps, 
        "studies_found_count": studies_found_count, 
        "studies_found": studies_found, 
        "uid": uid,
        "search_attempt_count": search_attempt_count,
        "next_step": next_step
    }