from chains.prompt_distiller_chain import prompt_distiller_chain
from utils import write_markdown_file

def prompt_distiller(state):
    """take the initial prompt and return a search term"""
    print("---DISTILLING INITIAL PROMPT---")
    initial_prompt = state['initial_prompt']
    num_steps = int(state['num_steps'])
    num_steps += 1

    search_term = prompt_distiller_chain.invoke({"initial_prompt": initial_prompt})
    print("___SEARCH TERM___ ", search_term)
    # save to local disk
    write_markdown_file(search_term, "search_term")

    return {"search_term": search_term, "num_steps":num_steps}
