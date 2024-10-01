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
        
        # Ask user if they want to use this search term or input their own
        user_choice = input("Do you want to use this search term? (yes/no): ").lower().strip()
        
        if user_choice == 'yes':
            if new_search_term not in current_search_terms:
                current_search_terms.append(new_search_term)
                break
            else:
                print(f"Search term '{new_search_term}' already exists. Generating a new one...")
        elif user_choice == 'no':
            user_search_term = input("Please enter your own search term: ").strip()
            if user_search_term and user_search_term not in current_search_terms:
                current_search_terms.append(user_search_term)
                print(f"Added user-provided search term: {user_search_term}")
                break
            elif user_search_term in current_search_terms:
                print(f"Search term '{user_search_term}' already exists. Please try again.")
            else:
                print("Invalid input. Please try again.")
        else:
            print("Invalid input. Please answer 'yes' or 'no'.")
    
    # Update the state with the new list of search terms
    updated_state = dict(state)  # Create a new copy of the state
    updated_state["search_term"] = current_search_terms
    updated_state["num_steps"] = num_steps
    
    # Save to local disk
    write_markdown_file(", ".join(current_search_terms), "search_terms")

    print("LIST OF SEARCH TERMS::: ", state.get("search_term", []))

    # Return the updated state
    return updated_state