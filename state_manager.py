from graph import create_workflow, GraphState
from LLMs.llm import GROQ_LLM
def initialize_state(uid):
    workflow = create_workflow(GROQ_LLM)
    state = GraphState(
        medical_report="",
        search_term=[],
        chat_history=[],
        final_medical_report="",
        research_info=[],
        follow_up="",
        num_steps=0,
        next_step="consultant",
        did_find_trials="",
        rag_questions=[],
        keep_searching = "",
        studies_found=0,
        uid = str(uid)
    )
    return state
