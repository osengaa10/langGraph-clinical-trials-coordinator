from utils import clinical_trials_search, write_markdown_file

def trials_search(state):
    """make api call to search for trials"""
    print("---FETCHING CLINICAL TRIALS---")
    search_term = state['search_term'][-1]
    state['search_term'].append(search_term)
    num_steps = int(state['num_steps'])
    num_steps += 1
    uid = state['uid']

    print("___UID___ ", uid)
    studies_found = clinical_trials_search(search_term.replace("\"", ""), uid)
    studies_found_count = len(studies_found)

    # save to local disk
    write_markdown_file(search_term, "search_term")

    return {"search_term": state['search_term'], "num_steps": num_steps, "studies_found_count": studies_found_count, "studies_found": studies_found, "uid": uid}