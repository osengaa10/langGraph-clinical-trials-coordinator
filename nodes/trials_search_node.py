from utils import clinical_trials_search, write_markdown_file



def trials_search(state):
    """make api call to search for trials"""
    print("---FETCHING CLINICAL TRIALS---")
    search_term = state['search_term']
    num_steps = int(state['num_steps'])
    num_steps += 1

    # search_term = trials_search_chain.invoke({"search_term": search_term})
    print("___SEARCH TERM BEFORE TRIALS SEARCH___ ", search_term)

    clinical_trials_search(search_term)

    # save to local disk
    write_markdown_file(search_term, "search_term")

    return {"search_term": search_term, "num_steps":num_steps}

