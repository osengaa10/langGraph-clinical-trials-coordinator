from chains.evaluate_trials_chain import evaluate_trials_chain
from langchain_core.runnables import RunnablePassthrough

def evaluate_research_info(state):
    print("---EVALUATING RESEARCH INFO---")
    research_info = state["research_info"][0]
    num_steps = state['num_steps']
    num_steps += 1

    # Use the evaluation chain to determine if a trial was found
    evaluation_result = evaluate_trials_chain.invoke({"research_info": research_info})
    
    if "A suitable clinical trial was found:" in evaluation_result:
        print("Clinical trial found.")
        print(evaluation_result)
        
        while True:
            user_response = input("Do you want to keep searching? (yes/no): ").lower().strip()
            if user_response in ['yes', 'no']:
                break
            print("Please answer with 'yes' or 'no'.")
        
        if user_response == 'yes':
            print("Continuing search. Returning to consultant.")
            next_step = "consultant"
            follow_up = "Let's explore more options. Can you provide any additional details about your condition or preferences for treatment?"
        else:
            print("Search complete. Proceeding to state printer.")
            next_step = "state_printer"
            follow_up = ""
    else:
        print("No suitable clinical trial found. Updating follow-up information.")
        follow_up = evaluation_result.split("Additional information needed:")[1].strip()
        next_step = "consultant"
        print(f"follow_up::: {follow_up}")
    return {
        "next_step": next_step,
        "num_steps": num_steps,
        "follow_up": follow_up
    }